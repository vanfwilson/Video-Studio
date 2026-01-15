import json
from app.services.openrouter import chat_completion

SYSTEM_PROMPT = """You generate YouTube-ready metadata from video transcripts.
Your output helps creators publish engaging content optimized for discovery.

Return STRICT JSON only. No markdown fences. No commentary.
"""

USER_TEMPLATE = """Using the transcript/captions below, generate YouTube metadata:

Requirements:
- title: Engaging, under 70 characters, hooks viewer interest
- description: 200-400 words, includes:
  - Hook in first line
  - Key points covered
  - Call to action
  - Relevant links placeholder [LINK]
- tags: 8-12 relevant keywords, comma-separated
- hashtags: 3-5 relevant hashtags, space-separated (e.g., #business #strategy)
- ai_summary: 3-5 bullet points summarizing the content
- thumbnail_prompt: Short descriptive prompt for thumbnail image generation (no copyrighted characters)

Return JSON:
{{
  "title": "...",
  "description": "...",
  "tags": "tag1, tag2, tag3",
  "hashtags": "#hashtag1 #hashtag2",
  "ai_summary": "• Point 1\\n• Point 2\\n• Point 3",
  "thumbnail_prompt": "..."
}}

Content to analyze:
{content}
"""


def _extract_json(raw: str) -> dict:
    """Extract JSON object from potentially messy model output."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(raw[start:end+1])


async def generate_metadata(content: str) -> tuple[dict, str]:
    """
    Generate YouTube metadata from video content.
    
    Returns:
        tuple: (metadata_dict, model_used)
    """
    # Limit content length
    truncated = content[:20000] if len(content) > 20000 else content
    
    result = await chat_completion(
        system=SYSTEM_PROMPT,
        user=USER_TEMPLATE.format(content=truncated),
        temperature=0.6  # Slightly higher for creative output
    )
    
    parsed = _extract_json(result["raw"])
    return parsed, result["model"]
