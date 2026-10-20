
"""Coordinate validation and execution through the media controller."""

from typing import Any, Protocol

from src.models import (
    IntentResult,
    MediaActionResult,
    ValidationResult,
)


class MediaController(Protocol):
    """Interface expected from Hemant's media controller."""

    def execute(self, intent: str) -> dict[str, Any]:
        """Execute a normalized intent and return a result dictionary."""
        ...


def execute_validated_command(
    validation: ValidationResult,
    controller: MediaController,
) -> MediaActionResult:
    """Execute only accepted intents and normalize controller results."""

    if not validation.allowed or validation.intent is None:
        return MediaActionResult(
            success=False,
            status=f"rejected:{validation.reason}",
        )

    intent_result: IntentResult = validation.intent
    intent = intent_result.intent

    if not isinstance(intent, str) or not intent:
        return MediaActionResult(
            success=False,
            status="rejected:invalid_intent",
        )

    try:
        result = controller.execute(intent)

        if not isinstance(result, dict):
            return MediaActionResult(
                success=False,
                status="controller_error:invalid_result",
            )

        success = result.get("success")
        status = result.get("status")

        if not isinstance(success, bool) or not isinstance(status, str):
            return MediaActionResult(
                success=False,
                status="controller_error:invalid_result",
            )

        return MediaActionResult(
            success=success,
            status=status,
        )

    except Exception:
        # Do not expose internal exception details to the caller.
        return MediaActionResult(
            success=False,
            status="controller_error:execution_failed",
        )
