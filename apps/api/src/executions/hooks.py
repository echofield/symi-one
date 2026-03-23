from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.executions.service import ExecutionService
from src.webhooks.outbound import emit_execution_events


async def notify_after_pipeline(db: AsyncSession, agreement_id: UUID) -> None:
    """Call after validation pipeline completes (same session)."""
    svc = ExecutionService(db)
    await svc.sync_from_agreement(agreement_id)
    await emit_execution_events(db, agreement_id)


async def notify_after_funding(db: AsyncSession, agreement_id: UUID) -> None:
    """Call after Stripe authorizes funds (same session)."""
    svc = ExecutionService(db)
    await svc.sync_from_agreement(agreement_id)
    await emit_execution_events(db, agreement_id)
