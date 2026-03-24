"""Arbitration configs and disputes

Revision ID: 003
Revises: 002
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute(
        """
        CREATE TYPE tieresolution AS ENUM (
            'payer_wins',
            'payee_wins',
            'split',
            'escalate'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE timeoutresolution AS ENUM (
            'release_to_payee',
            'return_to_payer',
            'escalate'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE disputetype AS ENUM (
            'proof_invalid',
            'proof_incomplete',
            'evaluation_error',
            'terms_misinterpretation',
            'fraud'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE disputestatus AS ENUM (
            'initiated',
            'evidence_submitted',
            'under_review',
            'resolved',
            'escalated'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE disputeresolution AS ENUM (
            'payer_wins',
            'payee_wins',
            'split',
            'voided'
        )
        """
    )

    # Create arbitration_configs table
    op.create_table(
        "arbitration_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("terms_hash", sa.String(64), nullable=False),
        sa.Column(
            "tie_breaker",
            postgresql.ENUM(
                "payer_wins",
                "payee_wins",
                "split",
                "escalate",
                name="tieresolution",
                create_type=False,
            ),
            nullable=False,
            server_default="escalate",
        ),
        sa.Column(
            "timeout_resolution",
            postgresql.ENUM(
                "release_to_payee",
                "return_to_payer",
                "escalate",
                name="timeoutresolution",
                create_type=False,
            ),
            nullable=False,
            server_default="escalate",
        ),
        sa.Column("dispute_window_hours", sa.BigInteger(), nullable=False, server_default="72"),
        sa.Column("terms_url", sa.Text(), nullable=True),
        sa.Column("payer_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payee_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_arbitration_configs_agreement", "arbitration_configs", ["agreement_id"], unique=True)

    # Create disputes table
    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("initiated_by", sa.String(64), nullable=False),
        sa.Column("initiated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "dispute_type",
            postgresql.ENUM(
                "proof_invalid",
                "proof_incomplete",
                "evaluation_error",
                "terms_misinterpretation",
                "fraud",
                name="disputetype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "initiated",
                "evidence_submitted",
                "under_review",
                "resolved",
                "escalated",
                name="disputestatus",
                create_type=False,
            ),
            nullable=False,
            server_default="initiated",
        ),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("counter_claim", sa.Text(), nullable=True),
        sa.Column(
            "resolution",
            postgresql.ENUM(
                "payer_wins",
                "payee_wins",
                "split",
                "voided",
                name="disputeresolution",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_disputes_agreement", "disputes", ["agreement_id"])
    op.create_index("idx_disputes_status", "disputes", ["status"])


def downgrade() -> None:
    op.drop_index("idx_disputes_status", table_name="disputes")
    op.drop_index("idx_disputes_agreement", table_name="disputes")
    op.drop_table("disputes")

    op.drop_index("idx_arbitration_configs_agreement", table_name="arbitration_configs")
    op.drop_table("arbitration_configs")

    op.execute("DROP TYPE disputeresolution")
    op.execute("DROP TYPE disputestatus")
    op.execute("DROP TYPE disputetype")
    op.execute("DROP TYPE timeoutresolution")
    op.execute("DROP TYPE tieresolution")
