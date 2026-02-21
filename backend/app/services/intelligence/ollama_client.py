"""Client for Ollama-hosted local LLM models."""

import json

import httpx

from app.config import settings
from app.utils.logging import logger


class OllamaClient:
    """Interface to Ollama API for local LLM inference."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
    ):
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a completion from the local LLM."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
            },
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.HTTPError as e:
            logger.error(f"Ollama request failed: {e}")
            raise RuntimeError(f"Ollama API error: {e}")

    async def analyze_transcript(self, transcript_text: str) -> list[dict]:
        """Ask the local LLM to analyze transcript for weak segments."""
        system_prompt = (
            "You are a video editing assistant. Analyze the following transcript "
            "and identify segments that should be removed or improved. "
            "Return a JSON array of objects with: "
            "start_marker (quote from text), end_marker (quote from text), "
            "action (remove/flag), reason (brief explanation), confidence (0-1)."
        )

        prompt = f"""Analyze this transcript and identify weak segments:

{transcript_text}

Return ONLY a valid JSON array. No other text."""

        response_text = await self.generate(prompt, system=system_prompt)

        try:
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ollama response as JSON")
            return []

    async def review_edit_plan(
        self, transcript_text: str, edit_plan: list[dict]
    ) -> list[dict]:
        """Review and refine an edit plan using local LLM (replaces Claude)."""
        system_prompt = (
            "You are an expert video editor. Review the edit plan and transcript. "
            "Confirm good edits, adjust bad ones, and add any missed cuts. "
            "Return ONLY a valid JSON array."
        )

        prompt = f"""Review this edit plan for a video transcript.

Transcript:
{transcript_text[:4000]}

Current edit plan:
{json.dumps(edit_plan, indent=2)}

For each edit, confirm or adjust. Add any edits the plan missed.
Return a JSON array of edit objects with: start, end, action, reason, confidence, source.
Set source to "ollama" for your additions.
Return ONLY valid JSON array."""

        try:
            response_text = await self.generate(prompt, system=system_prompt)
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])
            return edit_plan
        except (json.JSONDecodeError, RuntimeError) as e:
            logger.warning(f"Ollama edit plan review failed: {e}")
            return edit_plan

    async def check_health(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def pull_model(self, model: str | None = None) -> bool:
        """Pull a model if it's not already available."""
        model = model or self.model
        try:
            # Check if model exists
            response = await self.client.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                tags = response.json()
                existing = [m.get("name", "") for m in tags.get("models", [])]
                if any(model in name for name in existing):
                    logger.info(f"Ollama model '{model}' already available")
                    return True

            # Pull the model
            logger.info(f"Pulling Ollama model '{model}'... (this may take a while)")
            pull_response = await self.client.post(
                f"{self.host}/api/pull",
                json={"name": model, "stream": False},
                timeout=600.0,  # 10 min for large model downloads
            )
            pull_response.raise_for_status()
            logger.info(f"Ollama model '{model}' pulled successfully")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to pull Ollama model '{model}': {e}")
            return False

    async def ensure_models_ready(self) -> dict:
        """Ensure all configured models are pulled and ready."""
        results = {}
        models_to_pull = {settings.ollama_model, settings.ollama_reviewer_model}
        for model in models_to_pull:
            results[model] = await self.pull_model(model)
        return results

    async def close(self):
        await self.client.aclose()
