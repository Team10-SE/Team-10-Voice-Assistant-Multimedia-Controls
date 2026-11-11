
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
    # Play
    "play": "PLAY",
    "play music": "PLAY",
    "start playing": "PLAY",
    "start playback": "PLAY",
    "start music": "PLAY",
    "start the music": "PLAY",
    "play the song": "PLAY",

    # Pause
    "pause": "PAUSE",
    "pause playback": "PAUSE",
    "pause music": "PAUSE",

    # Resume
    "resume": "RESUME",
    "resume playback": "RESUME",
    "continue playback": "RESUME",
    "resume music": "RESUME",
    "continue playing": "RESUME",

    # Stop
    "stop": "STOP",
    "stop playback": "STOP",
    "stop music": "STOP",

    # Next and previous
    "next": "NEXT",
    "next track": "NEXT",
    "next song": "NEXT",
    "skip track": "NEXT",
    "skip song": "NEXT",
    "go to next track": "NEXT",
    "previous": "PREVIOUS",
    "previous track": "PREVIOUS",
    "previous song": "PREVIOUS",
    "go to previous track": "PREVIOUS",
    "go back a track": "PREVIOUS",

    # Volume
    "volume up": "VOLUME_UP",
    "increase volume": "VOLUME_UP",
    "turn volume up": "VOLUME_UP",
    "turn the volume up": "VOLUME_UP",
    "turn it up": "VOLUME_UP",
    "louder": "VOLUME_UP",
    "make it louder": "VOLUME_UP",
    "full volume": "VOLUME_UP",
    "max volume": "VOLUME_UP",
    "volume down": "VOLUME_DOWN",
    "decrease volume": "VOLUME_DOWN",
    "turn volume down": "VOLUME_DOWN",
    "turn the volume down": "VOLUME_DOWN",
    "turn it down": "VOLUME_DOWN",
    "softer": "VOLUME_DOWN",
    "quieter": "VOLUME_DOWN",
    "make it quieter": "VOLUME_DOWN",
    "minimum volume": "VOLUME_DOWN",

    # Mute
    "mute": "MUTE",
    "mute audio": "MUTE",
    "mute the sound": "MUTE",
    "unmute": "MUTE",
    "unmute audio": "MUTE",
    "unmute the sound": "MUTE",
    "sound on": "MUTE",
}

POLITE_PREFIXES = (
    "could you please ",
    "would you please ",
    "can you please ",
    "will you please ",
    "could you ",
    "would you ",
    "can you ",
    "will you ",
    "please ",
    "hey assistant ",
)


def normalize_text(text):
    """Normalize text for consistent phrase matching."""
    if not isinstance(text, str):
        return ""

    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return " ".join(text.split())


def detect_intent(text: str) -> IntentResult:
    """Return a structured intent result or an empty result."""
    phrase = normalize_text(text)

    if not phrase:
        return IntentResult(intent=None, parameters={})

    # Remove polite introductions without removing arbitrary words.
    changed = True
    while changed:
        changed = False

        for prefix in POLITE_PREFIXES:
            if phrase.startswith(prefix):
                phrase = phrase[len(prefix):].strip()
                changed = True
                break

    # Also support a polite suffix.
    if phrase.endswith(" please"):
        phrase = phrase[:-7].strip()

    intent = PHRASE_MAP.get(phrase)

    if intent not in SUPPORTED_INTENTS:
        return IntentResult(intent=None, parameters={})

    return IntentResult(intent=intent, parameters={})
