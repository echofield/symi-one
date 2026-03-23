from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidatorResult:
    """Result from a validator."""
    passed: bool
    reason: str
    score: float | None = None
    metadata: dict[str, Any] | None = None


class BaseValidator(ABC):
    """Base class for all validators."""

    @property
    @abstractmethod
    def validator_type(self) -> str:
        """Return the unique type identifier for this validator."""
        pass

    @abstractmethod
    async def validate(self, proof: Any, config: dict) -> ValidatorResult:
        """
        Validate the proof against the config.

        Args:
            proof: The proof to validate (URL string or file metadata)
            config: The validation configuration

        Returns:
            ValidatorResult with pass/fail and details
        """
        pass
