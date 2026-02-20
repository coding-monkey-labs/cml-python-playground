"""Claude API integration for strategic transcript review."""

import json

import anthropic

from app.config import settings
from app.utils.logging import logger


class ClaudeReviewer:
    """Uses Claude API for high-level transcript analysis."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def review_transcript(self, transcript_text: str) -> dict:
        """Send transcript to Claude for strategic review.

        Returns structured feedback on:
        - Structural weaknesses
        - Suggested removals
        - Hook evaluation
        """
        if not settings.anthropic_api_key:
            logger.warning("Claude API key not configured, skipping review")
            return {"enabled": False, "suggestions": []}

        system_prompt = (
            "You are an expert video editor and content strategist. "
            "Analyze the following video transcript and provide structured feedback."
        )

        user_prompt = f"""Analyze this video transcript and provide feedback in JSON format:

{transcript_text}

Return a JSON object with:
{{
  "structural_weaknesses": [
    {{
      "location": "beginning/middle/end",
      "description": "what's wrong",
      "severity": "high/medium/low"
    }}
  ],
  "suggested_removals": [
    {{
      "text_snippet": "exact text to remove",
      "reason": "why it should be removed",
      "confidence": 0.0-1.0
    }}
  ],
  "hook_evaluation": {{
    "score": 0.0-1.0,
    "feedback": "evaluation of the opening hook",
    "suggestion": "how to improve"
  }},
  "overall_quality": 0.0-1.0,
  "key_improvements": ["list of top improvements"]
}}

Return ONLY valid JSON."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = response.content[0].text

            # Parse JSON from response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])

            logger.warning("Could not parse Claude response as JSON")
            return {"enabled": True, "raw_response": response_text, "suggestions": []}

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return {"enabled": True, "error": str(e), "suggestions": []}

    async def evaluate_edit_plan(
        self, transcript_text: str, edit_plan: list[dict]
    ) -> list[dict]:
        """Have Claude review and refine an existing edit plan."""
        if not settings.anthropic_api_key:
            return edit_plan

        prompt = f"""Review this edit plan for a video transcript.

Transcript:
{transcript_text[:3000]}

Current edit plan:
{json.dumps(edit_plan, indent=2)}

For each edit, confirm or adjust. Add any edits the plan missed.
Return a JSON array of edit objects with: start, end, action, reason, confidence, source.
Set source to "claude" for your additions.
Return ONLY valid JSON array."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])
            return edit_plan

        except (anthropic.APIError, json.JSONDecodeError) as e:
            logger.error(f"Claude edit plan review failed: {e}")
            return edit_plan
