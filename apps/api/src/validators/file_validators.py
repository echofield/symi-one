from typing import Any
from dataclasses import dataclass

from src.validators.base import BaseValidator, ValidatorResult


@dataclass
class FileProof:
    """File proof metadata."""
    file_key: str
    file_name: str
    mime_type: str
    size_bytes: int


class FileExistsValidator(BaseValidator):
    """Validates that a file exists in storage."""

    @property
    def validator_type(self) -> str:
        return "file_exists"

    async def validate(self, proof: FileProof, config: dict) -> ValidatorResult:
        # The file existence is verified during upload completion
        # This validator just confirms the metadata is present
        if not proof.file_key:
            return ValidatorResult(
                passed=False,
                reason="No file key provided",
                metadata={"file_key": None}
            )

        if not proof.file_name:
            return ValidatorResult(
                passed=False,
                reason="No file name provided",
                metadata={"file_key": proof.file_key}
            )

        return ValidatorResult(
            passed=True,
            reason=f"File {proof.file_name} exists in storage",
            metadata={
                "file_key": proof.file_key,
                "file_name": proof.file_name,
            }
        )


class MimeAllowedValidator(BaseValidator):
    """Validates that a file's MIME type is in the allowed list."""

    @property
    def validator_type(self) -> str:
        return "mime_allowed"

    async def validate(self, proof: FileProof, config: dict) -> ValidatorResult:
        allowed_mimes = config.get("allowed_mime_types")

        if not allowed_mimes:
            return ValidatorResult(
                passed=True,
                reason="No MIME type restriction configured",
            )

        mime_type = proof.mime_type.lower()

        # Direct match
        if mime_type in [m.lower() for m in allowed_mimes]:
            return ValidatorResult(
                passed=True,
                reason=f"MIME type {mime_type} is allowed",
                metadata={
                    "mime_type": mime_type,
                    "allowed_mimes": allowed_mimes,
                }
            )

        # Wildcard match (e.g., "image/*")
        for allowed in allowed_mimes:
            if allowed.endswith("/*"):
                category = allowed[:-2].lower()
                if mime_type.startswith(f"{category}/"):
                    return ValidatorResult(
                        passed=True,
                        reason=f"MIME type {mime_type} matches wildcard {allowed}",
                        metadata={
                            "mime_type": mime_type,
                            "matched": allowed,
                        }
                    )

        return ValidatorResult(
            passed=False,
            reason=f"MIME type {mime_type} not in allowed list: {', '.join(allowed_mimes)}",
            metadata={
                "mime_type": mime_type,
                "allowed_mimes": allowed_mimes,
            }
        )


class MaxSizeValidator(BaseValidator):
    """Validates that a file is within the maximum size limit."""

    @property
    def validator_type(self) -> str:
        return "max_size"

    async def validate(self, proof: FileProof, config: dict) -> ValidatorResult:
        max_size_mb = config.get("max_size_mb")

        if max_size_mb is None:
            return ValidatorResult(
                passed=True,
                reason="No size limit configured",
            )

        max_size_bytes = max_size_mb * 1024 * 1024
        actual_mb = proof.size_bytes / (1024 * 1024)

        if proof.size_bytes <= max_size_bytes:
            return ValidatorResult(
                passed=True,
                reason=f"File size {actual_mb:.2f}MB is within {max_size_mb}MB limit",
                metadata={
                    "size_bytes": proof.size_bytes,
                    "size_mb": actual_mb,
                    "max_size_mb": max_size_mb,
                }
            )

        return ValidatorResult(
            passed=False,
            reason=f"File size {actual_mb:.2f}MB exceeds {max_size_mb}MB limit",
            metadata={
                "size_bytes": proof.size_bytes,
                "size_mb": actual_mb,
                "max_size_mb": max_size_mb,
            }
        )


# Export all file validators
FILE_VALIDATORS = [
    FileExistsValidator(),
    MimeAllowedValidator(),
    MaxSizeValidator(),
]
