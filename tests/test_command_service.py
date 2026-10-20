
import unittest

from src.command_service import execute_validated_command
from src.models import IntentResult, ValidationResult


class FakeMediaController:
    """Test double following Hemant's controller interface."""

    def __init__(self, response=None, should_raise=False):
        self.received = []
        self.response = response or {
            "success": True,
            "status": "Playing track 1: sample.mp3",
        }
        self.should_raise = should_raise

    def execute(self, intent: str) -> dict:
        self.received.append(intent)

        if self.should_raise:
            raise RuntimeError("simulated controller failure")

        return self.response


class TestCommandService(unittest.TestCase):
    def test_accepted_command_passes_intent_string(self):
        controller = FakeMediaController()
        validation = ValidationResult(
            True, IntentResult("PLAY", {}), "accepted"
        )

        result = execute_validated_command(validation, controller)

        self.assertTrue(result.success)
        self.assertEqual(controller.received, ["PLAY"])
        self.assertEqual(result.status, "Playing track 1: sample.mp3")

    def test_rejected_command_never_reaches_controller(self):
        controller = FakeMediaController()
        validation = ValidationResult(False, None, "low_confidence")

        result = execute_validated_command(validation, controller)

        self.assertFalse(result.success)
        self.assertEqual(result.status, "rejected:low_confidence")
        self.assertEqual(controller.received, [])

    def test_controller_failure_is_handled(self):
        controller = FakeMediaController(should_raise=True)
        validation = ValidationResult(
            True, IntentResult("PAUSE", {}), "accepted"
        )

        result = execute_validated_command(validation, controller)

        self.assertFalse(result.success)
        self.assertEqual(
            result.status, "controller_error:execution_failed"
        )

    def test_malformed_controller_result_is_rejected(self):
        controller = FakeMediaController(response={"unexpected": "data"})
        validation = ValidationResult(
            True, IntentResult("STOP", {}), "accepted"
        )

        result = execute_validated_command(validation, controller)

        self.assertFalse(result.success)
        self.assertEqual(result.status, "controller_error:invalid_result")


if __name__ == "__main__":
    unittest.main()
