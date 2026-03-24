"""Challenges and Stripe Connect accounts

Revision ID: 004
Revises: 003
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create challenge-related enums
    op.execute(
        """
        CREATE TYPE challengetype AS ENUM (
            'simple_bet',
            'fitness',
            'delivery',
            'accountability',
            'custom'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE challengestatus AS ENUM (
            'pending_acceptance',
            'active',
            'awaiting_proof',
            'resolving',
            'resolved',
            'disputed',
            'cancelled',
            'expired'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE challengeresolutiontype AS ENUM (
            'party_a_wins',
            'party_b_wins',
            'draw',
            'disputed',
            'expired'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE challengeprooftype AS ENUM (
            'attestation',
            'file',
            'url',
            'api',
            'check_in'
        )
        """
    )

    # Create connected_accounts table (Stripe Connect Express)
    op.create_table(
        "connected_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("stripe_account_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("charges_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("payouts_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("details_submitted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("default_currency", sa.String(3), nullable=True, server_default="'eur'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Create challenges table
    op.create_table(
        "challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("public_id", sa.String(16), nullable=False, unique=True, index=True),
        # Challenge definition
        sa.Column(
            "challenge_type",
            postgresql.ENUM(
                "simple_bet", "fitness", "delivery", "accountability", "custom",
                name="challengetype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("conditions_json", postgresql.JSON(), nullable=False, server_default="{}"),
        # Parties
        sa.Column("party_a_id", sa.String(128), nullable=False, index=True),
        sa.Column("party_b_id", sa.String(128), nullable=True, index=True),
        sa.Column("party_a_email", sa.String(255), nullable=False),
        sa.Column("party_b_email", sa.String(255), nullable=True),
        sa.Column("party_a_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connected_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("party_b_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connected_accounts.id", ondelete="SET NULL"), nullable=True),
        # Stakes
        sa.Column("stake_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="'eur'"),
        sa.Column("platform_fee_percent", sa.Numeric(5, 2), nullable=False, server_default="10.00"),  # 10% visible platform fee
        # Stripe PaymentIntents
        sa.Column("party_a_payment_intent_id", sa.String(64), nullable=True, index=True),
        sa.Column("party_b_payment_intent_id", sa.String(64), nullable=True, index=True),
        sa.Column("party_a_funded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("party_b_funded", sa.Boolean(), nullable=False, server_default="false"),
        # Status & resolution
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending_acceptance", "active", "awaiting_proof", "resolving",
                "resolved", "disputed", "cancelled", "expired",
                name="challengestatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending_acceptance",
        ),
        sa.Column("winner_id", sa.String(128), nullable=True),
        sa.Column(
            "resolution_type",
            postgresql.ENUM(
                "party_a_wins", "party_b_wins", "draw", "disputed", "expired",
                name="challengeresolutiontype",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        # Arbitration config
        sa.Column("dispute_window_hours", sa.BigInteger(), nullable=False, server_default="24"),
        sa.Column("timeout_resolution", sa.String(32), nullable=False, server_default="'split'"),
        # Timing
        sa.Column("proof_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acceptance_deadline", sa.DateTime(timezone=True), nullable=True),
        # Invite
        sa.Column("invite_token", sa.String(64), nullable=False, unique=True, index=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_challenges_status", "challenges", ["status"])
    op.create_index("idx_challenges_created", "challenges", ["created_at"])

    # Create challenge_proofs table
    op.create_table(
        "challenge_proofs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("submitted_by", sa.String(128), nullable=False),
        # Proof content
        sa.Column(
            "proof_type",
            postgresql.ENUM(
                "attestation", "file", "url", "api", "check_in",
                name="challengeprooftype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("proof_data", postgresql.JSON(), nullable=False),
        sa.Column("proof_hash", sa.String(64), nullable=False),
        # Attestation specific
        sa.Column("attested_outcome", sa.String(32), nullable=True),
        # File specific
        sa.Column("file_key", sa.String(512), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        # URL specific
        sa.Column("url", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_challenge_proofs_submitted_by", "challenge_proofs", ["submitted_by"])

    # Create challenge_events table (audit trail)
    op.create_table(
        "challenge_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_challenge_events_type", "challenge_events", ["event_type"])


def downgrade() -> None:
    # Drop tables
    op.drop_index("idx_challenge_events_type", table_name="challenge_events")
    op.drop_table("challenge_events")

    op.drop_index("idx_challenge_proofs_submitted_by", table_name="challenge_proofs")
    op.drop_table("challenge_proofs")

    op.drop_index("idx_challenges_created", table_name="challenges")
    op.drop_index("idx_challenges_status", table_name="challenges")
    op.drop_table("challenges")

    op.drop_table("connected_accounts")

    # Drop enums
    op.execute("DROP TYPE challengeprooftype")
    op.execute("DROP TYPE challengeresolutiontype")
    op.execute("DROP TYPE challengestatus")
    op.execute("DROP TYPE challengetype")
