
"""Map recognized text to predefined multimedia intents."""

import re

from src.models import IntentResult


SUPPORTED_INTENTS = {
    "PLAY",
    "PAUSE",
    "RESUME",
    "STOP",
    "NEXT",
    "PREVIOUS",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "MUTE",
}

PHRASE_MAP = {
    "play": "PLAY",
    "start playback": "PLAY",
    "pause": "PAUSE",
    "pause playback": "PAUSE",
    "resume": "RESUME",
    "resume playback": "RESUME",
    "continue playback": "RESUME",
    "stop": "STOP",
    "stop playback": "STOP",
    "next": "NEXT",
    "next track": "NEXT",
    "next song": "NEXT",
    "previous": "PREVIOUS",
    "previous track": "PREVIOUS",
    "previous song": "PREVIOUS",
    "volume up": "VOLUME_UP",
    "increase volume": "VOLUME_UP",
    "volume down": "VOLUME_DOWN",
    "decrease volume": "VOLUME_DOWN",
    "mute": "MUTE",
    "mute audio": "MUTE",
}


def detect_intent(text: str) -> IntentResult:
    """Return a structured intent result or an empty result."""
    if not isinstance(text, str) or not text.strip():
        return IntentResult(intent=None, parameters={})

    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    phrase = " ".join(normalized.split())
    intent = PHRASE_MAP.get(phrase)

    if intent not in SUPPORTED_INTENTS:
        return IntentResult(intent=None, parameters={})

    return IntentResult(intent=intent, parameters={})
