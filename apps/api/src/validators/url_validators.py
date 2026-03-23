import httpx
from urllib.parse import urlparse
from typing import Any

from src.validators.base import BaseValidator, ValidatorResult


class UrlReachableValidator(BaseValidator):
    """Validates that a URL is reachable and returns HTTP 200."""

    @property
    def validator_type(self) -> str:
        return "url_reachable"

    async def validate(self, proof: str, config: dict) -> ValidatorResult:
        require_200 = config.get("require_status_200", True)

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(proof)

                if require_200 and response.status_code != 200:
                    return ValidatorResult(
                        passed=False,
                        reason=f"URL returned status {response.status_code}, expected 200",
                        metadata={
                            "status_code": response.status_code,
                            "url": proof,
                        }
                    )

                # Accept any 2xx status if not requiring 200 specifically
                if not require_200 and not (200 <= response.status_code < 300):
                    return ValidatorResult(
                        passed=False,
                        reason=f"URL returned non-success status {response.status_code}",
                        metadata={
                            "status_code": response.status_code,
                            "url": proof,
                        }
                    )

                return ValidatorResult(
                    passed=True,
                    reason=f"URL is reachable with status {response.status_code}",
                    metadata={
                        "status_code": response.status_code,
                        "url": proof,
                        "content_type": response.headers.get("content-type"),
                    }
                )

        except httpx.TimeoutException:
            return ValidatorResult(
                passed=False,
                reason="URL request timed out after 30 seconds",
                metadata={"url": proof, "error": "timeout"}
            )
        except httpx.RequestError as e:
            return ValidatorResult(
                passed=False,
                reason=f"Failed to reach URL: {str(e)}",
                metadata={"url": proof, "error": str(e)}
            )
        except Exception as e:
            return ValidatorResult(
                passed=False,
                reason=f"Unexpected error validating URL: {str(e)}",
                metadata={"url": proof, "error": str(e)}
            )


class DomainAllowlistValidator(BaseValidator):
    """Validates that a URL is from an allowed domain."""

    @property
    def validator_type(self) -> str:
        return "domain_allowlist"

    async def validate(self, proof: str, config: dict) -> ValidatorResult:
        allowed_domains = config.get("allowed_domains")

        if not allowed_domains:
            return ValidatorResult(
                passed=True,
                reason="No domain restriction configured",
            )

        try:
            parsed = urlparse(proof)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]

            # Check if domain matches any allowed domain
            for allowed in allowed_domains:
                allowed = allowed.lower()
                # Allow exact match or subdomain match
                if domain == allowed or domain.endswith(f".{allowed}"):
                    return ValidatorResult(
                        passed=True,
                        reason=f"Domain {domain} is in allowlist",
                        metadata={
                            "domain": domain,
                            "matched": allowed,
                        }
                    )

            return ValidatorResult(
                passed=False,
                reason=f"Domain {domain} is not in allowlist: {', '.join(allowed_domains)}",
                metadata={
                    "domain": domain,
                    "allowed_domains": allowed_domains,
                }
            )

        except Exception as e:
            return ValidatorResult(
                passed=False,
                reason=f"Failed to parse URL: {str(e)}",
                metadata={"url": proof, "error": str(e)}
            )


class LighthouseScoreValidator(BaseValidator):
    """
    Validates that a URL meets a minimum Lighthouse performance score.
    Note: This is a simplified implementation that checks basic performance indicators.
    For full Lighthouse support, integrate with the Lighthouse API or run the CLI.
    """

    @property
    def validator_type(self) -> str:
        return "lighthouse_score"

    async def validate(self, proof: str, config: dict) -> ValidatorResult:
        min_score = config.get("min_lighthouse_score")

        if min_score is None:
            return ValidatorResult(
                passed=True,
                reason="No Lighthouse score requirement configured",
            )

        # Simplified check: measure response time and size
        # In production, integrate with actual Lighthouse API
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                import time
                start = time.time()
                response = await client.get(proof)
                elapsed = time.time() - start

                # Simple scoring based on response time and size
                # Real Lighthouse has much more sophisticated metrics
                content_length = len(response.content)
                time_score = max(0, 100 - (elapsed * 20))  # -20 points per second
                size_score = max(0, 100 - (content_length / 100000))  # -1 point per 100KB

                estimated_score = (time_score + size_score) / 2

                if estimated_score >= min_score:
                    return ValidatorResult(
                        passed=True,
                        reason=f"Estimated performance score {estimated_score:.0f} meets minimum {min_score}",
                        score=estimated_score,
                        metadata={
                            "url": proof,
                            "response_time_ms": elapsed * 1000,
                            "content_length": content_length,
                            "estimated_score": estimated_score,
                            "note": "Simplified estimation. Use Lighthouse API for accurate scoring.",
                        }
                    )
                else:
                    return ValidatorResult(
                        passed=False,
                        reason=f"Estimated performance score {estimated_score:.0f} below minimum {min_score}",
                        score=estimated_score,
                        metadata={
                            "url": proof,
                            "response_time_ms": elapsed * 1000,
                            "content_length": content_length,
                            "estimated_score": estimated_score,
                            "required_score": min_score,
                        }
                    )

        except Exception as e:
            return ValidatorResult(
                passed=False,
                reason=f"Failed to measure performance: {str(e)}",
                metadata={"url": proof, "error": str(e)}
            )


# Export all URL validators
URL_VALIDATORS = [
    UrlReachableValidator(),
    DomainAllowlistValidator(),
    LighthouseScoreValidator(),
]
