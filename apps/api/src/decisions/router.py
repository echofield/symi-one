from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from src.db.models import DecisionLog
from src.decisions.schemas import DecisionLogResponse, DecisionListResponse


router = APIRouter(tags=["decisions"])


@router.get("", response_model=DecisionListResponse)
async def list_decisions(
    agreement_id: UUID | None = Query(None, description="Filter by agreement"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List decision logs with optional filtering.

    Admin endpoint for viewing the audit trail.
    """
    query = select(DecisionLog)
    count_query = select(func.count(DecisionLog.id))

    if agreement_id:
        query = query.where(DecisionLog.agreement_id == agreement_id)
        count_query = count_query.where(DecisionLog.agreement_id == agreement_id)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get decisions
    result = await db.execute(
        query
        .order_by(DecisionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    decisions = list(result.scalars().all())

    return DecisionListResponse(
        decisions=[DecisionLogResponse.model_validate(d) for d in decisions],
        total=total
    )


@router.get("/{decision_id}", response_model=DecisionLogResponse)
async def get_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific decision log entry.
    """
    result = await db.execute(
        select(DecisionLog).where(DecisionLog.id == decision_id)
    )
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return DecisionLogResponse.model_validate(decision)
