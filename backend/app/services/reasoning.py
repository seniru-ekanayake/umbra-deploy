import json
import logging
from typing import Dict, Optional

import httpx
from app.core.config import settings

logger = logging.getLogger("umbra.reasoning")


# =========================
# SAFE JSON PARSER
# =========================

def safe_parse(text: str) -> Optional[Dict]:
    try:
        return json.loads(text)
    except Exception:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
        except Exception:
            return None
    return None


# =========================
# MOCK FALLBACK
# =========================

def mock_reasoning(gap_data):
    return {
        "attacker_path": f"Attackers exploit {gap_data.get('technique_id')} due to missing visibility.",
        "detection_failure": "Detection fails because required telemetry is missing or broken.",
        "estimated_dwell_time": "30–90 days depending on attacker sophistication.",
        "business_impact": "High risk of lateral movement, data exfiltration, and persistence."
    }


# =========================
# MAIN FUNCTION
# =========================

async def generate_gap_reasoning(
    gap_data: Dict,
    client_data: Dict,
    technique_data: Dict,
    rule_data: Dict,
    source_data: Dict,
) -> Optional[Dict]:

    # No API key → fallback
    if not settings.ANTHROPIC_API_KEY:
        return mock_reasoning(gap_data)

    prompt = f"""
You are a senior cybersecurity detection engineer.

Return ONLY valid JSON. No markdown. No explanation.

Format:
{{
  "attacker_path": "...",
  "detection_failure": "...",
  "estimated_dwell_time": "...",
  "business_impact": "..."
}}

Context:
Client: {client_data.get("name")}
Industry: {client_data.get("industry")}
Technique: {gap_data.get("technique_id")}
Gap Type: {gap_data.get("gap_type")}
Missing Sources: {gap_data.get("missing_sources")}
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-3-haiku-20241022",
                    "max_tokens": 800,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                },
            )

        # Handle API errors cleanly
        if response.status_code != 200:
            logger.error(f"Claude API error: {response.status_code} {response.text}")
            return mock_reasoning(gap_data)

        data = response.json()

        text_output = data.get("content", [{}])[0].get("text", "")

        parsed = safe_parse(text_output)

        if parsed:
            return parsed

        logger.error("Claude JSON parse failed — falling back to mock")
        return mock_reasoning(gap_data)

    except Exception as e:
        logger.error(f"Claude API error: {e} — falling back to mock")
        return mock_reasoning(gap_data)
