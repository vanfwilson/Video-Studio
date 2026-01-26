#!/usr/bin/env python3
"""
Caption translation service using OpenRouter API with DeepSeek v3.
Translates SRT captions to multiple languages while preserving timing.
"""

import os
import re
import json
import httpx
from typing import Optional

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-chat"  # DeepSeek V3

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "hi": "Hindi",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
}


def parse_srt(srt_content: str) -> list[dict]:
    """Parse SRT content into a list of subtitle entries."""
    entries = []
    blocks = re.split(r'\n\n+', srt_content.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timing = lines[1]
                text = '\n'.join(lines[2:])
                entries.append({
                    "index": index,
                    "timing": timing,
                    "text": text
                })
            except (ValueError, IndexError):
                continue

    return entries


def format_srt(entries: list[dict]) -> str:
    """Format subtitle entries back to SRT format."""
    srt_lines = []
    for entry in entries:
        srt_lines.append(str(entry["index"]))
        srt_lines.append(entry["timing"])
        srt_lines.append(entry["text"])
        srt_lines.append("")
    return '\n'.join(srt_lines)


def translate_text_batch(
    texts: list[str],
    target_language: str,
    source_language: str = "English",
    model: str = DEFAULT_MODEL,
) -> list[str]:
    """
    Translate a batch of texts using OpenRouter API.
    Returns translations in the same order as input.
    """
    if not texts:
        return []

    target_lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)

    # Create numbered list for batch translation
    numbered_texts = [f"{i+1}. {text}" for i, text in enumerate(texts)]
    batch_text = "\n".join(numbered_texts)

    prompt = f"""Translate the following {source_language} subtitles to {target_lang_name}.
Keep the same numbered format. Only output the translations, nothing else.
Preserve any line breaks within each subtitle.
Do not add any explanations or notes.

{batch_text}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://video-studio.askstephen.ai",
        "X-Title": "Video Studio Caption Translator"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional subtitle translator. Translate accurately while preserving meaning and tone. Keep translations concise for subtitle readability."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }

    response = httpx.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120.0
    )
    response.raise_for_status()

    result = response.json()
    translated_text = result["choices"][0]["message"]["content"].strip()

    # Parse numbered translations back
    translations = []
    lines = translated_text.split('\n')
    current_num = 1
    current_text = []

    for line in lines:
        # Check if this line starts a new numbered item
        match = re.match(r'^(\d+)\.\s*(.*)$', line)
        if match:
            num = int(match.group(1))
            if num == current_num + 1 and current_text:
                translations.append('\n'.join(current_text))
                current_text = []
            current_num = num
            current_text.append(match.group(2))
        elif current_text:
            current_text.append(line)

    if current_text:
        translations.append('\n'.join(current_text))

    # Ensure we have the right number of translations
    while len(translations) < len(texts):
        translations.append(texts[len(translations)])  # Use original if translation missing

    return translations[:len(texts)]


def translate_srt(
    srt_content: str,
    target_language: str,
    source_language: str = "en",
    model: str = DEFAULT_MODEL,
    batch_size: int = 20,
) -> str:
    """
    Translate entire SRT content to target language.
    Processes in batches to handle long videos.
    """
    entries = parse_srt(srt_content)
    if not entries:
        return srt_content

    source_lang_name = SUPPORTED_LANGUAGES.get(source_language, "English")

    # Extract texts for translation
    texts = [entry["text"] for entry in entries]

    # Translate in batches
    translated_texts = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"Translating batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
        translated_batch = translate_text_batch(
            batch,
            target_language,
            source_lang_name,
            model
        )
        translated_texts.extend(translated_batch)

    # Update entries with translations
    for i, entry in enumerate(entries):
        if i < len(translated_texts):
            entry["text"] = translated_texts[i]

    return format_srt(entries)


def translate_captions_to_languages(
    srt_content: str,
    target_languages: list[str],
    source_language: str = "en",
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """
    Translate captions to multiple languages.
    Returns dict mapping language code to translated SRT content.
    """
    results = {}

    for lang in target_languages:
        if lang == source_language:
            results[lang] = srt_content
            continue

        print(f"Translating to {SUPPORTED_LANGUAGES.get(lang, lang)}...")
        try:
            translated = translate_srt(srt_content, lang, source_language, model)
            results[lang] = translated
        except Exception as e:
            print(f"Error translating to {lang}: {e}")
            results[lang] = None

    return results


def main():
    """CLI interface for caption translation."""
    import argparse

    parser = argparse.ArgumentParser(description="Translate SRT captions using AI")
    parser.add_argument("input_file", help="Input SRT file")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--target", "-t", required=True, help="Target language code (e.g., es, fr, de)")
    parser.add_argument("--source", "-s", default="en", help="Source language code (default: en)")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--list-languages", action="store_true", help="List supported languages")

    args = parser.parse_args()

    if args.list_languages:
        print("Supported languages:")
        for code, name in sorted(SUPPORTED_LANGUAGES.items()):
            print(f"  {code}: {name}")
        return

    with open(args.input_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    translated = translate_srt(
        srt_content,
        args.target,
        args.source,
        args.model
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(translated)
        print(f"Translated captions saved to {args.output}")
    else:
        print(translated)


if __name__ == "__main__":
    main()
