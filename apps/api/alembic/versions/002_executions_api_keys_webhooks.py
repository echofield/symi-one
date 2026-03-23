"""Executions, API keys, outbound webhooks

Revision ID: 002
Revises: 001
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE executionstatus AS ENUM (
            'created',
            'awaiting_funding',
            'awaiting_proof',
            'validating',
            'manual_review',
            'failed',
            'paid',
            'cancelled'
        )
        """
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("prefix", sa.String(16), unique=True, nullable=False, index=True),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default="default"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("public_id", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "created",
                "awaiting_funding",
                "awaiting_proof",
                "validating",
                "manual_review",
                "failed",
                "paid",
                "cancelled",
                name="executionstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="created",
        ),
        sa.Column("next_action", sa.String(64), nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_executions_api_key_idempotency", "executions", ["api_key_id", "idempotency_key"], unique=True)

    op.create_table(
        "webhook_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("webhook_endpoints")
    op.drop_index("idx_executions_api_key_idempotency", table_name="executions")
    op.drop_table("executions")
    op.drop_table("api_keys")
    op.execute("DROP TYPE executionstatus")
