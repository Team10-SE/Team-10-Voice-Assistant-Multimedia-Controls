
import time

import pytest

from src.command_validator import validate_command
from src.command_service import execute_validated_command
from src.models import IntentResult, ValidationResult


class FakeMediaController:
    """Simulates the media controller without performing real actions."""

    def __init__(self, should_fail=False):
        self.calls = []
        self.should_fail = should_fail

    def execute(self, intent):
        self.calls.append(intent)

        if self.should_fail:
            raise RuntimeError("Simulated controller failure")

        return {
            "success": True,
            "status": "completed"
        }


# --------------------------------------------------
# RELIABILITY TESTS
# --------------------------------------------------

def test_repeated_command_execution():
    """Check whether repeated valid commands are processed."""

    controller = FakeMediaController()

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 0.95)

    for _ in range(100):
        outcome = execute_validated_command(
            validation, controller
        )
        assert outcome.success is True

    assert len(controller.calls) == 100
    assert all(call == "PLAY" for call in controller.calls)


def test_multiple_supported_commands():
    """Check that different supported intents reach the controller."""

    controller = FakeMediaController()

    intents = ["PLAY", "PAUSE", "STOP", "NEXT", "PREVIOUS"]

    for intent in intents:
        result = IntentResult(intent, {})
        validation = validate_command(result, 0.95)

        outcome = execute_validated_command(
            validation, controller
        )

        assert outcome.success is True

    assert controller.calls == intents


def test_controller_recovers_after_failure():
    """Check that a later command can execute after a failure."""

    failing_controller = FakeMediaController(should_fail=True)

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 0.95)

    failed_outcome = execute_validated_command(
        validation, failing_controller
    )

    assert failed_outcome.success is False

    working_controller = FakeMediaController()

    successful_outcome = execute_validated_command(
        validation, working_controller
    )

    assert successful_outcome.success is True
    assert working_controller.calls == ["PLAY"]


# --------------------------------------------------
# SECURITY TESTS
# --------------------------------------------------

@pytest.mark.parametrize(
    "malicious_intent",
    [
        "DELETE_FILES",
        "RUN_TERMINAL",
        "EXECUTE_SCRIPT",
        "ACCESS_PASSWORDS",
        "SYSTEM_SHUTDOWN",
    ]
)
def test_unsupported_malicious_intents_are_rejected(
    malicious_intent
):
    """Unsupported intents must never be executed."""

    result = IntentResult(malicious_intent, {})
    validation = validate_command(result, 0.99)

    assert validation.allowed is False
    assert validation.reason == "unsupported_intent"


def test_rejected_intent_never_reaches_controller():
    """A rejected intent must not reach the media controller."""

    controller = FakeMediaController()

    result = IntentResult("DELETE_FILES", {})
    validation = validate_command(result, 0.99)

    outcome = execute_validated_command(
        validation, controller
    )

    assert outcome.success is False
    assert controller.calls == []


def test_invalid_confidence_prevents_execution():
    """Invalid confidence must prevent command execution."""

    controller = FakeMediaController()

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 1.5)

    outcome = execute_validated_command(
        validation, controller
    )

    assert validation.allowed is False
    assert outcome.success is False
    assert controller.calls == []


# --------------------------------------------------
# PERFORMANCE MEASUREMENT
# --------------------------------------------------

def test_command_service_execution_time():
    """
    Measure command-service execution time.

    This measures the Python service call only.
    It does not measure microphone or speech recognition latency.
    """

    controller = FakeMediaController()

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 0.95)

    start_time = time.perf_counter()

    outcome = execute_validated_command(
        validation, controller
    )

    end_time = time.perf_counter()

    execution_time_ms = (end_time - start_time) * 1000

    print(
        f"\nCommand service execution time: "
        f"{execution_time_ms:.3f} ms"
    )

    assert outcome.success is True
    assert execution_time_ms >= 0


# --------------------------------------------------
# FAILURE HANDLING
# --------------------------------------------------

def test_repeated_controller_failures_are_handled():
    """Check that repeated controller failures return errors."""

    controller = FakeMediaController(should_fail=True)

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 0.95)

    for _ in range(5):
        outcome = execute_validated_command(
            validation, controller
        )

        assert outcome.success is False

    assert len(controller.calls) == 5


def test_controller_exception_details_are_not_exposed():
    """Check that internal exception details are not exposed."""

    controller = FakeMediaController(should_fail=True)

    result = IntentResult("PLAY", {})
    validation = validate_command(result, 0.95)

    outcome = execute_validated_command(
        validation, controller
    )

    assert outcome.success is False
    assert "Simulated controller failure" not in outcome.status
