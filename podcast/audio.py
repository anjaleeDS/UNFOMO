"""
Google Cloud TTS: renders the weekly podcast script to MP3.
Uses Journey voices for natural-sounding audio.
Splits the script by speaker ([ANJA] / [HOST]) and renders each turn
with a different voice for a two-host effect.
"""
import os
import re
import tempfile

from config import GOOGLE_CLOUD_TTS_KEY
from db import repository as db

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# Journey voices — natural, conversational
VOICE_ANJA = "en-US-Journey-F"   # female
VOICE_HOST = "en-US-Journey-D"   # male

TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


def _synthesize_segment(text: str, voice_name: str) -> bytes:
    """Call Google Cloud TTS REST API, return MP3 bytes."""
    import httpx, base64, json

    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "en-US",
            "name": voice_name,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.05,
        },
    }

    r = httpx.post(
        TTS_API_URL,
        params={"key": GOOGLE_CLOUD_TTS_KEY},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    audio_b64 = r.json()["audioContent"]
    return base64.b64decode(audio_b64)


def _parse_script(script: str) -> list[tuple[str, str]]:
    """
    Parse speaker turns from script.
    Returns list of (voice_name, text) tuples.
    """
    segments = []
    current_voice = VOICE_ANJA
    current_lines = []

    for line in script.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("[ANJA]"):
            if current_lines:
                segments.append((current_voice, " ".join(current_lines)))
                current_lines = []
            current_voice = VOICE_ANJA
            text = line[6:].strip()
            if text:
                current_lines.append(text)

        elif line.startswith("[HOST]"):
            if current_lines:
                segments.append((current_voice, " ".join(current_lines)))
                current_lines = []
            current_voice = VOICE_HOST
            text = line[6:].strip()
            if text:
                current_lines.append(text)

        elif line.startswith("[INTRO]"):
            text = line[7:].strip()
            if text:
                current_lines.append(text)

        else:
            current_lines.append(line)

    if current_lines:
        segments.append((current_voice, " ".join(current_lines)))

    return segments


def render_podcast(script: str, output_path: str = None) -> str | None:
    """
    Render a podcast script to MP3.
    Returns path to saved file, or None on failure.
    """
    if not GOOGLE_CLOUD_TTS_KEY:
        print("[tts] GOOGLE_CLOUD_TTS_KEY not set. Skipping audio render.")
        return None

    segments = _parse_script(script)
    if not segments:
        print("[tts] No segments parsed from script.")
        return None

    audio_chunks = []
    for i, (voice, text) in enumerate(segments):
        if not text.strip():
            continue
        try:
            chunk = _synthesize_segment(text[:5000], voice)  # TTS limit per call
            audio_chunks.append(chunk)
            print(f"[tts] Rendered segment {i+1}/{len(segments)}")
        except Exception as e:
            print(f"[tts] Error on segment {i+1}: {e}")
            continue

    if not audio_chunks:
        return None

    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        from datetime import date
        output_path = os.path.join(OUTPUT_DIR, f"unfomo_weekly_{date.today()}.mp3")

    # Concatenate MP3 chunks (simple binary concatenation works for MP3)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    print(f"[tts] Podcast saved → {output_path}")
    return output_path


def render_latest_weekly() -> str | None:
    """Render the most recent weekly digest's podcast script."""
    digest = db.get_latest_digest("weekly")
    if not digest or not digest.get("podcast_script"):
        print("[tts] No podcast script found in latest weekly digest.")
        return None

    path = render_podcast(digest["podcast_script"])
    if path:
        # Update digest record with audio path
        # (simple approach: insert a new digest with audio url)
        print(f"[tts] Done: {path}")
    return path


if __name__ == "__main__":
    render_latest_weekly()
