"""
Automated Unit Tests for Hemant's VLC Media Controller (T10VA-6)

Tests cover all 9 media intents, playlist wrap-around, volume boundaries,
mute toggling, error handling, and edge cases using pure fakes/mocks.
No physical microphone, speakers, VLC GUI, or Raspberry Pi hardware required.
"""

import os
from pathlib import Path
import pytest
from src.media_controller import MediaController


class FakeVLCMedia:
    """Fake VLC Media object."""

    def __init__(self, mrl: str):
        self.mrl = mrl


class FakeVLCPlayer:
    """Fake VLC MediaPlayer simulating playback, pause, stop, and volume states."""

    def __init__(self):
        self.media = None
        self.state = "STOPPED"
        self.volume = 0
        self.muted = False
        self.play_called = 0
        self.stop_called = 0
        self.fail_play = False
        self.raise_on_play = False
        self.fail_volume = False
        self.raise_on_volume = False
        self.fail_mute = False
        self.raise_on_mute = False
        self.raise_on_pause = False
        self.raise_on_stop = False

    def set_media(self, media):
        self.media = media

    def play(self):
        if self.raise_on_play:
            raise RuntimeError("Underlying libVLC fatal crash")
        if self.fail_play:
            return -1
        self.state = "PLAYING"
        self.play_called += 1
        return 0

    def pause(self):
        if self.raise_on_pause:
            raise RuntimeError("Underlying libVLC pause crash")
        if self.state == "PLAYING":
            self.state = "PAUSED"
        elif self.state == "PAUSED":
            self.state = "PLAYING"

    def set_pause(self, do_pause: int):
        if self.raise_on_pause:
            raise RuntimeError("Underlying libVLC pause crash")
        self.state = "PAUSED" if do_pause else "PLAYING"

    def stop(self):
        if self.raise_on_stop:
            raise RuntimeError("Underlying libVLC stop crash")
        self.state = "STOPPED"
        self.stop_called += 1

    def is_playing(self) -> int:
        return 1 if self.state == "PLAYING" else 0

    def audio_set_volume(self, vol: int):
        if self.raise_on_volume:
            raise RuntimeError("Hardware mixer communication error")
        if self.fail_volume:
            return -1
        self.volume = vol
        return 0

    def audio_set_mute(self, mute: bool):
        if self.raise_on_mute:
            raise RuntimeError("Hardware mute line disconnected")
        if self.fail_mute:
            return -1
        self.muted = bool(mute)
        return 0


class FakeVLCInstance:
    """Fake VLC Instance providing media creation."""

    def __init__(self):
        pass

    def media_new(self, path: str):
        return FakeVLCMedia(path)


@pytest.fixture
def mock_files(tmp_path: Path):
    """Create three temporary media files for deterministic testing."""
    f1 = tmp_path / "song1.mp3"
    f2 = tmp_path / "song2.mp3"
    f3 = tmp_path / "song3.mp3"
    f1.write_bytes(b"ID3fake1")
    f2.write_bytes(b"ID3fake2")
    f3.write_bytes(b"ID3fake3")
    return [str(f1), str(f2), str(f3)]


@pytest.fixture
def controller(mock_files):
    """Return a MediaController configured with fakes."""
    fake_inst = FakeVLCInstance()
    fake_player = FakeVLCPlayer()
    return MediaController(
        media_files=mock_files,
        vlc_instance=fake_inst,
        player=fake_player,
    )


# =========================================================================
# 1. Initialization and Contract Tests
# =========================================================================

def test_controller_initialization(controller, mock_files):
    """Verify default initialization values."""
    assert controller.media_files == mock_files
    assert controller.current_index == 0
    assert controller.volume == 70
    assert controller.is_muted is False
    assert controller.is_paused() is False
    assert controller.is_playing() is False
    assert controller.get_current_track() == mock_files[0]


def test_execute_intent_normalization(controller):
    """Verify intent execution is case-insensitive and trims whitespace."""
    res = controller.execute("  play  ")
    assert res["success"] is True
    assert "Playing track 1" in res["status"]


def test_execute_invalid_or_empty_intent(controller):
    """Verify invalid and non-string intents return controlled failures."""
    res1 = controller.execute("")
    assert res1["success"] is False
    assert "Invalid or empty" in res1["status"]

    res2 = controller.execute(None)  # type: ignore
    assert res2["success"] is False
    assert "Invalid or empty" in res2["status"]

    res3 = controller.execute(123)  # type: ignore
    assert res3["success"] is False


def test_execute_unsupported_intent(controller):
    """Verify unknown intents are rejected with controlled failure."""
    res = controller.execute("FAST_FORWARD")
    assert res["success"] is False
    assert "Unsupported media intent: 'FAST_FORWARD'" in res["status"]


# =========================================================================
# 2. Sprint 1 Priority Commands: PLAY, PAUSE, RESUME
# =========================================================================

def test_play_success(controller, mock_files):
    """Verify PLAY starts playback of the first track."""
    res = controller.execute("PLAY")
    assert res["success"] is True
    assert "song1.mp3" in res["status"]
    assert controller.player.state == "PLAYING"
    assert controller.is_playing() is True


def test_pause_success(controller):
    """Verify PAUSE pauses active playback."""
    controller.execute("PLAY")
    res = controller.execute("PAUSE")
    assert res["success"] is True
    assert "Paused: song1.mp3" in res["status"]
    assert controller.is_paused() is True
    assert controller.player.state == "PAUSED"


def test_pause_when_already_paused(controller):
    """Verify PAUSE when already paused reports idempotently."""
    controller.execute("PLAY")
    controller.execute("PAUSE")
    res = controller.execute("PAUSE")
    assert res["success"] is True
    assert "already paused" in res["status"]


def test_pause_when_stopped(controller):
    """Verify PAUSE when not playing returns controlled failure."""
    res = controller.execute("PAUSE")
    assert res["success"] is False
    assert "No active media playback" in res["status"]


def test_resume_from_paused(controller):
    """Verify RESUME unpauses paused media."""
    controller.execute("PLAY")
    controller.execute("PAUSE")
    assert controller.is_paused() is True

    res = controller.execute("RESUME")
    assert res["success"] is True
    assert "Resumed playback: song1.mp3" in res["status"]
    assert controller.is_paused() is False
    assert controller.player.state == "PLAYING"


def test_resume_when_already_playing(controller):
    """Verify RESUME when actively playing returns success with status."""
    controller.execute("PLAY")
    res = controller.execute("RESUME")
    assert res["success"] is True
    assert "Playback already in progress" in res["status"]


def test_resume_when_unstarted(controller):
    """Verify RESUME when not yet playing starts playback of track 1."""
    res = controller.execute("RESUME")
    assert res["success"] is True
    assert "Playing track 1" in res["status"]


# =========================================================================
# 3. STOP, NEXT, PREVIOUS and Playlist Boundary Wrap-Around
# =========================================================================

def test_stop_playback(controller):
    """Verify STOP halts playback and clears paused state."""
    controller.execute("PLAY")
    controller.execute("PAUSE")
    res = controller.execute("STOP")
    assert res["success"] is True
    assert "Playback stopped." in res["status"]
    assert controller.player.state == "STOPPED"
    assert controller.is_paused() is False


def test_next_track_sequential(controller, mock_files):
    """Verify NEXT advances to track 2, then track 3."""
    controller.execute("PLAY")
    res1 = controller.execute("NEXT")
    assert res1["success"] is True
    assert controller.current_index == 1
    assert "song2.mp3" in res1["status"]

    res2 = controller.execute("NEXT")
    assert res2["success"] is True
    assert controller.current_index == 2
    assert "song3.mp3" in res2["status"]


def test_next_track_wraparound_last_to_first(controller, mock_files):
    """Verify NEXT wraps around from the last track to the first track."""
    controller.execute("PLAY")
    controller.execute("NEXT")  # index 1
    controller.execute("NEXT")  # index 2 (last track)
    assert controller.current_index == 2

    # Wrap-around from 2 back to 0
    res = controller.execute("NEXT")
    assert res["success"] is True
    assert controller.current_index == 0
    assert "song1.mp3" in res["status"]


def test_previous_track_wraparound_first_to_last(controller, mock_files):
    """Verify PREVIOUS wraps around from the first track (index 0) to the last track."""
    assert controller.current_index == 0
    # From index 0, PREVIOUS should wrap to index 2 (len - 1)
    res = controller.execute("PREVIOUS")
    assert res["success"] is True
    assert controller.current_index == 2
    assert "song3.mp3" in res["status"]


def test_previous_track_sequential_backward(controller, mock_files):
    """Verify PREVIOUS moves backward from track 3 to track 2."""
    controller.execute("PREVIOUS")  # index 2
    assert controller.current_index == 2

    res = controller.execute("PREVIOUS")  # index 1
    assert res["success"] is True
    assert controller.current_index == 1
    assert "song2.mp3" in res["status"]


# =========================================================================
# 4. Volume Increment, Decrement, and Limits (Inclusive 0–100%)
# =========================================================================

def test_volume_up_increment(controller):
    """Verify VOLUME_UP increments volume by 10%."""
    assert controller.volume == 70
    res = controller.execute("VOLUME_UP")
    assert res["success"] is True
    assert controller.volume == 80
    assert "Volume increased to 80%" in res["status"]
    assert controller.player.volume == 80


def test_volume_up_clamp_at_100(controller):
    """Verify VOLUME_UP cannot exceed inclusive 100% maximum."""
    controller.execute("VOLUME_UP")  # 80
    controller.execute("VOLUME_UP")  # 90
    controller.execute("VOLUME_UP")  # 100
    assert controller.volume == 100

    # Beyond 100 clamp
    res = controller.execute("VOLUME_UP")
    assert res["success"] is True
    assert controller.volume == 100
    assert "Volume increased to 100%" in res["status"]


def test_volume_down_decrement(controller):
    """Verify VOLUME_DOWN decrements volume by 10%."""
    assert controller.volume == 70
    res = controller.execute("VOLUME_DOWN")
    assert res["success"] is True
    assert controller.volume == 60
    assert "Volume decreased to 60%" in res["status"]
    assert controller.player.volume == 60


def test_volume_down_clamp_at_0(controller):
    """Verify VOLUME_DOWN cannot go below inclusive 0% minimum."""
    for _ in range(8):
        controller.execute("VOLUME_DOWN")
    assert controller.volume == 0

    # Beyond 0 clamp
    res = controller.execute("VOLUME_DOWN")
    assert res["success"] is True
    assert controller.volume == 0
    assert "Volume decreased to 0%" in res["status"]


# =========================================================================
# 5. MUTE Toggling
# =========================================================================

def test_mute_toggle_on_and_off(controller):
    """Verify MUTE predictably toggles mute state between True and False."""
    assert controller.is_muted is False

    # First toggle: Mute ON
    res1 = controller.execute("MUTE")
    assert res1["success"] is True
    assert controller.is_muted is True
    assert "Audio muted." in res1["status"]
    assert controller.player.muted is True

    # Second toggle: Mute OFF
    res2 = controller.execute("MUTE")
    assert res2["success"] is True
    assert controller.is_muted is False
    assert "Audio unmuted." in res2["status"]
    assert controller.player.muted is False


# =========================================================================
# 6. Edge Cases, Empty Playlist, Missing Files, and Error Handling
# =========================================================================

def test_empty_playlist_handling():
    """Verify empty playlist returns controlled failures."""
    ctrl = MediaController(media_files=[], vlc_instance=FakeVLCInstance(), player=FakeVLCPlayer())

    res_play = ctrl.execute("PLAY")
    assert res_play["success"] is False
    assert "Playlist is empty" in res_play["status"]

    res_next = ctrl.execute("NEXT")
    assert res_next["success"] is False
    assert "Playlist is empty" in res_next["status"]

    res_prev = ctrl.execute("PREVIOUS")
    assert res_prev["success"] is False
    assert "Playlist is empty" in res_prev["status"]


def test_missing_media_file_handling():
    """Verify missing/non-existent media file returns controlled failure."""
    ctrl = MediaController(
        media_files=["/non/existent/path/song.mp3"],
        vlc_instance=FakeVLCInstance(),
        player=FakeVLCPlayer(),
    )
    res = ctrl.execute("PLAY")
    assert res["success"] is False
    assert "Media file not found" in res["status"]


def test_vlc_player_failure_code(controller):
    """Verify player.play() returning -1 is reported cleanly."""
    controller.player.fail_play = True
    res = controller.execute("PLAY")
    assert res["success"] is False
    assert "Failed to start playback" in res["status"]
    assert "error_details" in res


def test_vlc_player_runtime_exception(controller):
    """Verify underlying player exception is caught, returns controlled status, and preserves diagnostics."""
    controller.player.raise_on_play = True
    res = controller.execute("PLAY")
    assert res["success"] is False
    assert res["status"] == "Failed to start media playback."
    assert "Underlying libVLC fatal crash" not in res["status"]
    assert "Underlying libVLC fatal crash" in res["error_details"]


def test_vlc_unavailable_error():
    """Verify behavior for all commands when VLC is not available."""
    ctrl = MediaController(media_files=["dummy.mp3"], vlc_instance=None, player=None)
    ctrl.vlc_available = False
    ctrl.player = None

    for cmd in ["PLAY", "PAUSE", "RESUME", "STOP", "VOLUME_UP", "VOLUME_DOWN", "MUTE"]:
        res = ctrl.execute(cmd)
        assert res["success"] is False
        assert "unavailable" in res["status"]
        assert "error_details" in res


# =========================================================================
# 7. Focused Failure Tests: Volume & Mute Failures (VLC Unavailable & API Errors)
# =========================================================================

def test_volume_up_when_vlc_unavailable():
    """Verify VOLUME_UP returns controlled failure when VLC player is unavailable."""
    ctrl = MediaController(media_files=["song.mp3"], vlc_instance=None, player=None)
    ctrl.vlc_available = False
    ctrl.player = None

    res = ctrl.execute("VOLUME_UP")
    assert res["success"] is False
    assert "VLC media player is unavailable" in res["status"]
    assert "error_details" in res
    assert ctrl.volume == 70


def test_volume_down_when_vlc_unavailable():
    """Verify VOLUME_DOWN returns controlled failure when VLC player is unavailable."""
    ctrl = MediaController(media_files=["song.mp3"], vlc_instance=None, player=None)
    ctrl.vlc_available = False
    ctrl.player = None

    res = ctrl.execute("VOLUME_DOWN")
    assert res["success"] is False
    assert "VLC media player is unavailable" in res["status"]
    assert "error_details" in res
    assert ctrl.volume == 70


def test_mute_when_vlc_unavailable():
    """Verify MUTE returns controlled failure when VLC player is unavailable."""
    ctrl = MediaController(media_files=["song.mp3"], vlc_instance=None, player=None)
    ctrl.vlc_available = False
    ctrl.player = None

    res = ctrl.execute("MUTE")
    assert res["success"] is False
    assert "VLC media player is unavailable" in res["status"]
    assert "error_details" in res
    assert ctrl.is_muted is False


def test_volume_up_when_audio_api_returns_error_code(controller):
    """Verify VOLUME_UP fails cleanly when player.audio_set_volume returns -1."""
    controller.player.fail_volume = True
    initial_volume = controller.volume

    res = controller.execute("VOLUME_UP")
    assert res["success"] is False
    assert res["status"] == "Failed to increase volume."
    assert "error_details" in res
    assert controller.volume == initial_volume


def test_volume_up_when_audio_api_raises_exception(controller):
    """Verify VOLUME_UP fails cleanly without exposing exception when player raises exception."""
    controller.player.raise_on_volume = True
    initial_volume = controller.volume

    res = controller.execute("VOLUME_UP")
    assert res["success"] is False
    assert res["status"] == "Failed to increase volume."
    assert "Hardware mixer communication error" not in res["status"]
    assert "Hardware mixer communication error" in res["error_details"]
    assert controller.volume == initial_volume


def test_volume_down_when_audio_api_returns_error_code(controller):
    """Verify VOLUME_DOWN fails cleanly when player.audio_set_volume returns -1."""
    controller.player.fail_volume = True
    initial_volume = controller.volume

    res = controller.execute("VOLUME_DOWN")
    assert res["success"] is False
    assert res["status"] == "Failed to decrease volume."
    assert "error_details" in res
    assert controller.volume == initial_volume


def test_volume_down_when_audio_api_raises_exception(controller):
    """Verify VOLUME_DOWN fails cleanly without exposing exception when player raises exception."""
    controller.player.raise_on_volume = True
    initial_volume = controller.volume

    res = controller.execute("VOLUME_DOWN")
    assert res["success"] is False
    assert res["status"] == "Failed to decrease volume."
    assert "Hardware mixer communication error" not in res["status"]
    assert "Hardware mixer communication error" in res["error_details"]
    assert controller.volume == initial_volume


def test_mute_when_audio_api_returns_error_code(controller):
    """Verify MUTE fails cleanly when player.audio_set_mute returns -1."""
    controller.player.fail_mute = True
    initial_mute = controller.is_muted

    res = controller.execute("MUTE")
    assert res["success"] is False
    assert res["status"] == "Failed to toggle audio mute."
    assert "error_details" in res
    assert controller.is_muted == initial_mute


def test_mute_when_audio_api_raises_exception(controller):
    """Verify MUTE fails cleanly without exposing exception when player raises exception."""
    controller.player.raise_on_mute = True
    initial_mute = controller.is_muted

    res = controller.execute("MUTE")
    assert res["success"] is False
    assert res["status"] == "Failed to toggle audio mute."
    assert "Hardware mute line disconnected" not in res["status"]
    assert "Hardware mute line disconnected" in res["error_details"]
    assert controller.is_muted == initial_mute


# =========================================================================
# 8. Controlled Error Messages: No Raw Exception Details in User Status
# =========================================================================

def test_pause_runtime_exception_controlled_message(controller):
    """Verify PAUSE failure does not expose raw exception text in user status."""
    controller.execute("PLAY")
    controller.player.raise_on_pause = True

    res = controller.execute("PAUSE")
    assert res["success"] is False
    assert res["status"] == "Failed to pause media playback."
    assert "Underlying libVLC pause crash" not in res["status"]
    assert "Underlying libVLC pause crash" in res["error_details"]


def test_resume_runtime_exception_controlled_message(controller):
    """Verify RESUME failure does not expose raw exception text in user status."""
    controller.execute("PLAY")
    controller.execute("PAUSE")
    controller.player.raise_on_pause = True

    res = controller.execute("RESUME")
    assert res["success"] is False
    assert res["status"] == "Failed to resume media playback."
    assert "Underlying libVLC pause crash" not in res["status"]
    assert "Underlying libVLC pause crash" in res["error_details"]


def test_stop_runtime_exception_controlled_message(controller):
    """Verify STOP failure does not expose raw exception text in user status."""
    controller.execute("PLAY")
    controller.player.raise_on_stop = True

    res = controller.execute("STOP")
    assert res["success"] is False
    assert res["status"] == "Failed to stop media playback."
    assert "Underlying libVLC stop crash" not in res["status"]
    assert "Underlying libVLC stop crash" in res["error_details"]


def test_no_raw_exception_exposed_in_user_facing_status(controller):
    """Verify that simulated internal errors never leak exception details to user status."""
    controller.player.raise_on_play = True
    res = controller.execute("PLAY")
    assert res["success"] is False
    assert "RuntimeError" not in res["status"]
    assert "crash" not in res["status"]
    assert "error_details" in res
