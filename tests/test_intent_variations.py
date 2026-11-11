import pytest

from src.intent_processor import detect_intent


@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("please play music", "PLAY"),
        ("could you please play music", "PLAY"),
        ("can you pause music", "PAUSE"),
        ("next song", "NEXT"),
        ("turn the volume up", "VOLUME_UP"),
        ("turn the volume down", "VOLUME_DOWN"),
        ("turn volume up", "VOLUME_UP"),
        ("please mute audio", "MUTE"),
        ("unmute", "MUTE"),
        ("please unmute audio", "MUTE"),
        ("louder", "VOLUME_UP"),
        ("could you please make it louder", "VOLUME_UP"),
        ("softer", "VOLUME_DOWN"),
        ("make it quieter", "VOLUME_DOWN"),
        ("full volume", "VOLUME_UP"),
        ("max volume", "VOLUME_UP"),
        ("minimum volume", "VOLUME_DOWN"),
        ("sound on", "MUTE"),
        ("could you stop playback", "STOP"),
        ("dont play music", None),
        ("play music and stop", None),
        ("open browser", None),
        ("maybe pause the music", None),
        ("turn it", None),
        ("skip", None),
        ("play something and pause", None),
    ],
)
def test_intent_variations(phrase, expected):
    assert detect_intent(phrase).intent == expected
