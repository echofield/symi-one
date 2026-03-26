"""Add RELIABLE V0 models

Revision ID: 005
Revises: 004
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    execution_challenge_status = postgresql.ENUM(
        'open', 'active', 'resolving', 'resolved', 'cancelled',
        name='executionchallengestatus',
        create_type=True
    )
    execution_challenge_status.create(op.get_bind(), checkfirst=True)

    participation_status = postgresql.ENUM(
        'pending', 'active', 'completed', 'failed', 'withdrawn',
        name='participationstatus',
        create_type=True
    )
    participation_status.create(op.get_bind(), checkfirst=True)

    daily_proof_status = postgresql.ENUM(
        'submitted', 'validated', 'rejected',
        name='dailyproofstatus',
        create_type=True
    )
    daily_proof_status.create(op.get_bind(), checkfirst=True)

    # Create execution_challenges table
    op.create_table(
        'execution_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('public_id', sa.String(16), unique=True, nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proof_description', sa.Text(), nullable=False),
        sa.Column('proof_type', sa.String(32), nullable=False, default='url'),
        sa.Column('allowed_domains', postgresql.JSON(), nullable=True),
        sa.Column('duration_days', sa.BigInteger(), nullable=False, default=7),
        sa.Column('join_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('min_stake_cents', sa.BigInteger(), nullable=False, default=2000),
        sa.Column('max_stake_cents', sa.BigInteger(), nullable=False, default=10000),
        sa.Column('stake_options_cents', postgresql.JSON(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='eur'),
        sa.Column('pool_total_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('platform_fee_percent', sa.Numeric(5, 2), nullable=False, default=10.00),
        sa.Column('status', execution_challenge_status, nullable=False, default='open'),
        sa.Column('participant_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('active_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('completed_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('failed_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create challenge_participations table
    op.create_table(
        'challenge_participations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('challenge_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('execution_challenges.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.String(128), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('connected_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('connected_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stake_amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='eur'),
        sa.Column('payment_intent_id', sa.String(64), nullable=True, index=True),
        sa.Column('payment_status', sa.Enum('pending', 'authorized', 'captured', 'failed', 'cancelled', 'refunded', name='paymentstatus', create_type=False), nullable=False, default='pending'),
        sa.Column('status', participation_status, nullable=False, default='pending'),
        sa.Column('days_completed', sa.BigInteger(), nullable=False, default=0),
        sa.Column('current_streak', sa.BigInteger(), nullable=False, default=0),
        sa.Column('failed_on_day', sa.BigInteger(), nullable=True),
        sa.Column('payout_amount_cents', sa.BigInteger(), nullable=True),
        sa.Column('payout_transfer_id', sa.String(64), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create daily_proofs table
    op.create_table(
        'daily_proofs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('participation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('challenge_participations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('day_number', sa.BigInteger(), nullable=False),
        sa.Column('proof_type', sa.String(32), nullable=False),
        sa.Column('proof_url', sa.Text(), nullable=True),
        sa.Column('proof_image_key', sa.String(512), nullable=True),
        sa.Column('proof_hash', sa.String(64), nullable=False),
        sa.Column('status', daily_proof_status, nullable=False, default='submitted'),
        sa.Column('validation_details', postgresql.JSON(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create kernel_records table
    op.create_table(
        'kernel_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(128), nullable=False, index=True),
        sa.Column('challenge_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('execution_challenges.id', ondelete='SET NULL'), nullable=True),
        sa.Column('participation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('challenge_participations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('challenge_title', sa.String(255), nullable=False),
        sa.Column('challenge_type', sa.String(64), nullable=False, default='7_day_execution'),
        sa.Column('outcome', sa.String(32), nullable=False),
        sa.Column('days_completed', sa.BigInteger(), nullable=False),
        sa.Column('days_required', sa.BigInteger(), nullable=False),
        sa.Column('completion_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('stake_amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('payout_amount_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('net_result_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='eur'),
        sa.Column('proof_hashes', postgresql.JSON(), nullable=False),
        sa.Column('record_hash', sa.String(64), nullable=False),
        sa.Column('sealed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('signature', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create user_kernel_profiles table
    op.create_table(
        'user_kernel_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(128), unique=True, nullable=False, index=True),
        sa.Column('total_challenges', sa.BigInteger(), nullable=False, default=0),
        sa.Column('completed_challenges', sa.BigInteger(), nullable=False, default=0),
        sa.Column('failed_challenges', sa.BigInteger(), nullable=False, default=0),
        sa.Column('completion_rate', sa.Numeric(5, 4), nullable=False, default=0.0),
        sa.Column('total_staked_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('total_earned_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('total_lost_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('net_position_cents', sa.BigInteger(), nullable=False, default=0),
        sa.Column('currency', sa.String(3), nullable=False, default='eur'),
        sa.Column('current_streak', sa.BigInteger(), nullable=False, default=0),
        sa.Column('longest_streak', sa.BigInteger(), nullable=False, default=0),
        sa.Column('last_challenge_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create unique constraint for daily proofs (one per day per participation)
    op.create_index(
        'ix_daily_proofs_participation_day',
        'daily_proofs',
        ['participation_id', 'day_number'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_daily_proofs_participation_day', table_name='daily_proofs')
    op.drop_table('user_kernel_profiles')
    op.drop_table('kernel_records')
    op.drop_table('daily_proofs')
    op.drop_table('challenge_participations')
    op.drop_table('execution_challenges')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS dailyproofstatus')
    op.execute('DROP TYPE IF EXISTS participationstatus')
    op.execute('DROP TYPE IF EXISTS executionchallengestatus')
