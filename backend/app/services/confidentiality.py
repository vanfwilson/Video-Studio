import json
from datetime import datetime
from app.services.openrouter import chat_json

SYSTEM = """You are a confidentiality and compliance checker for video transcripts.
Return STRICT JSON only. No markdown. No commentary.
"""

USER_TEMPLATE = """Analyze this transcript for confidentiality risks:
- PII (phone, email, addresses)
- credentials/keys
- internal sensitive info
- client private info
- regulated data
Return JSON:
{
  "overall_status": "pass|warn|fail",
  "summary": "short summary",
  "counts": {"high": 0, "medium": 0, "low": 0},
  "segments": [
    {"risk":"high|medium|low","reason":"...","snippet":"..."}
  ]
}
Transcript:
{transcript}
"""

def _extract_json(raw: str) -> dict:
    # naive but effective: find first {...} block
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(raw[start:end+1])

async def run_confidentiality(transcript: str) -> tuple[dict, str]:
    res = await chat_json(SYSTEM, USER_TEMPLATE.format(transcript=transcript[:20000]))
    obj = _extract_json(res["raw"])
    return obj, res["model"]
