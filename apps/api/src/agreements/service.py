import secrets
import string
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models import Agreement, ValidationConfig, AgreementStatus, ProofType
from src.agreements.schemas import CreateAgreementRequest, UpdateAgreementRequest
from app.config import get_settings

settings = get_settings()


def generate_public_id(length: int = 8) -> str:
    """Generate a short public ID for agreements."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """Generate a secure URL token."""
    return secrets.token_urlsafe(length)


def get_validation_rules_description(proof_type: ProofType, config: dict) -> list[str]:
    """Convert validation config to human-readable rules."""
    rules = []

    if proof_type == ProofType.url:
        if config.get("require_status_200", True):
            rules.append("URL must return HTTP 200 status")
        if domains := config.get("allowed_domains"):
            rules.append(f"URL must be from: {', '.join(domains)}")
        if score := config.get("min_lighthouse_score"):
            rules.append(f"Lighthouse performance score must be at least {score}")
        if config.get("check_mobile_friendly"):
            rules.append("Page must be mobile-friendly")
    else:
        if mimes := config.get("allowed_mime_types"):
            rules.append(f"Allowed file types: {', '.join(mimes)}")
        if max_size := config.get("max_size_mb"):
            rules.append(f"Maximum file size: {max_size}MB")

    return rules if rules else ["Proof must be submitted before deadline"]


class AgreementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agreement(self, data: CreateAgreementRequest) -> Agreement:
        """Create a new agreement with validation config."""
        public_id = generate_public_id()
        funding_token = generate_token()
        submit_token = generate_token()

        agreement = Agreement(
            public_id=public_id,
            title=data.title,
            description=data.description,
            amount=data.amount,
            currency=data.currency.lower(),
            proof_type=ProofType(data.proof_type.value),
            status=AgreementStatus.draft,
            payer_email=data.payer_email,
            payee_email=data.payee_email,
            funding_url_token=funding_token,
            submit_url_token=submit_token,
            deadline_at=data.deadline_at,
        )

        self.db.add(agreement)
        await self.db.flush()

        validation_config = ValidationConfig(
            agreement_id=agreement.id,
            config_json=data.validation_config,
        )
        self.db.add(validation_config)

        await self.db.commit()
        await self.db.refresh(agreement)

        return agreement

    async def get_agreement(self, agreement_id: UUID) -> Agreement | None:
        """Get agreement by ID."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.validation_config))
            .options(selectinload(Agreement.payment))
            .where(Agreement.id == agreement_id)
        )
        return result.scalar_one_or_none()

    async def get_agreement_by_public_id(self, public_id: str) -> Agreement | None:
        """Get agreement by public ID."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.validation_config))
            .options(selectinload(Agreement.payment))
            .where(Agreement.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_agreement_by_funding_token(self, token: str) -> Agreement | None:
        """Get agreement by funding URL token."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.validation_config))
            .options(selectinload(Agreement.payment))
            .where(Agreement.funding_url_token == token)
        )
        return result.scalar_one_or_none()

    async def get_agreement_by_submit_token(self, token: str) -> Agreement | None:
        """Get agreement by submit URL token."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.validation_config))
            .options(selectinload(Agreement.payment))
            .options(selectinload(Agreement.submissions))
            .where(Agreement.submit_url_token == token)
        )
        return result.scalar_one_or_none()

    async def update_agreement(
        self,
        agreement_id: UUID,
        data: UpdateAgreementRequest
    ) -> Agreement | None:
        """Update an agreement."""
        agreement = await self.get_agreement(agreement_id)
        if not agreement:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agreement, field, value)

        agreement.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agreement)

        return agreement

    async def update_status(
        self,
        agreement_id: UUID,
        status: AgreementStatus
    ) -> Agreement | None:
        """Update agreement status."""
        agreement = await self.get_agreement(agreement_id)
        if not agreement:
            return None

        agreement.status = status
        agreement.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agreement)

        return agreement

    async def publish_agreement(self, agreement_id: UUID) -> Agreement | None:
        """Publish agreement (make it awaiting funding)."""
        agreement = await self.get_agreement(agreement_id)
        if not agreement:
            return None

        if agreement.status != AgreementStatus.draft:
            return None

        agreement.status = AgreementStatus.awaiting_funding
        agreement.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agreement)

        return agreement

    async def list_agreements(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[Agreement]:
        """List agreements."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.payment))
            .order_by(Agreement.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def get_funding_url(self, agreement: Agreement) -> str:
        """Get the public funding URL for an agreement."""
        return f"{settings.public_url}/a/{agreement.funding_url_token}"

    def get_submit_url(self, agreement: Agreement) -> str:
        """Get the proof submission URL for an agreement."""
        return f"{settings.public_url}/submit/{agreement.submit_url_token}"

    def get_public_info(self, agreement: Agreement) -> dict:
        """Get public-facing agreement info."""
        config = agreement.validation_config.config_json if agreement.validation_config else {}
        rules = get_validation_rules_description(agreement.proof_type, config)

        is_funded = agreement.status in [
            AgreementStatus.funded,
            AgreementStatus.proof_submitted,
            AgreementStatus.validating,
            AgreementStatus.passed,
            AgreementStatus.failed,
            AgreementStatus.manual_review_required,
            AgreementStatus.paid,
        ]

        return {
            "id": agreement.public_id,
            "title": agreement.title,
            "description": agreement.description,
            "amount": agreement.amount,
            "currency": agreement.currency,
            "proof_type": agreement.proof_type.value,
            "status": agreement.status.value,
            "deadline_at": agreement.deadline_at,
            "validation_rules": rules,
            "is_funded": is_funded,
            "payer_email": agreement.payer_email,
        }
