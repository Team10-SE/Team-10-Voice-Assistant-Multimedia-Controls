
"""Validate commands before they reach the media controller."""

from src.intent_processor import SUPPORTED_INTENTS
from src.models import IntentResult, ValidationResult


def validate_command(
    result: IntentResult,
    confidence: float,
    minimum_confidence: float = 0.70,
) -> ValidationResult:
    """Reject invalid, unsupported, or low-confidence commands."""

    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        return ValidationResult(False, None, "invalid_confidence")

    if not isinstance(result, IntentResult):
        return ValidationResult(False, None, "invalid_intent_result")

    if confidence < minimum_confidence:
        return ValidationResult(False, None, "low_confidence")

    if result.intent not in SUPPORTED_INTENTS:
        return ValidationResult(False, None, "unsupported_intent")

    return ValidationResult(True, result, "accepted")
