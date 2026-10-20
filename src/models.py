
"""Shared data structures for component integration."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecognitionResult:
    text: str
    confidence: float


@dataclass(frozen=True)
class IntentResult:
    intent: str | None
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ValidationResult:
    allowed: bool
    intent: IntentResult | None
    reason: str


@dataclass(frozen=True)
class MediaActionResult:
    success: bool
    status: str
