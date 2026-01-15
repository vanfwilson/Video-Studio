import json
from app.services.openrouter import chat_completion

SYSTEM_PROMPT = """You are a confidentiality and compliance checker for video transcripts.
Your job is to identify any sensitive information that should not be published publicly.

Return STRICT JSON only. No markdown fences. No commentary.
"""

USER_TEMPLATE = """Analyze this transcript for confidentiality risks:
- PII (phone numbers, email addresses, home addresses)
- Credentials, API keys, passwords
- Internal business-sensitive information
- Client private information
- Regulated data (HIPAA, financial, legal)
- Names of real people who may not have consented

Return JSON in this exact format:
{{
  "overall_status": "pass|warn|fail",
  "summary": "Brief one-line summary of findings",
  "counts": {{"high": 0, "medium": 0, "low": 0}},
  "segments": [
    {{"risk": "high|medium|low", "reason": "Why this is risky", "snippet": "The problematic text"}}
  ]
}}

If no issues found, return: {{"overall_status": "pass", "summary": "No confidentiality issues detected", "counts": {{"high": 0, "medium": 0, "low": 0}}, "segments": []}}

Transcript to analyze:
{transcript}
"""


def _extract_json(raw: str) -> dict:
    """Extract JSON object from potentially messy model output."""
    # Try to find JSON object
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    
    json_str = raw[start:end+1]
    return json.loads(json_str)


async def run_confidentiality_check(transcript: str) -> tuple[dict, str]:
    """
    Run confidentiality check on transcript.
    
    Returns:
        tuple: (result_dict, model_used)
        
    result_dict contains:
    - overall_status: "pass" | "warn" | "fail"
    - summary: Brief description
    - counts: {"high": int, "medium": int, "low": int}
    - segments: List of flagged segments
    """
    # Limit transcript length to avoid token limits
    truncated = transcript[:20000] if len(transcript) > 20000 else transcript
    
    result = await chat_completion(
        system=SYSTEM_PROMPT,
        user=USER_TEMPLATE.format(transcript=truncated)
    )
    
    parsed = _extract_json(result["raw"])
    return parsed, result["model"]
