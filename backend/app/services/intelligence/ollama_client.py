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
            # Try to extract JSON from the response
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ollama response as JSON")
            return []

    async def check_health(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self):
        await self.client.aclose()
