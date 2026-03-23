"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE prooftype AS ENUM ('url', 'file')")
    op.execute("""
        CREATE TYPE agreementstatus AS ENUM (
            'draft', 'awaiting_funding', 'funded', 'proof_submitted',
            'validating', 'passed', 'failed', 'manual_review_required',
            'paid', 'expired', 'cancelled'
        )
    """)
    op.execute("""
        CREATE TYPE paymentstatus AS ENUM (
            'pending', 'authorized', 'captured', 'failed', 'cancelled', 'refunded'
        )
    """)
    op.execute("""
        CREATE TYPE submissionstatus AS ENUM (
            'submitted', 'validating', 'passed', 'failed', 'manual_review_required'
        )
    """)
    op.execute("""
        CREATE TYPE decisiontype AS ENUM (
            'authorize_payment', 'reject_submission', 'request_manual_review', 'capture_payment'
        )
    """)
    op.execute("""
        CREATE TYPE decisionoutcome AS ENUM (
            'approved', 'rejected', 'manual_review', 'error'
        )
    """)
    op.execute("CREATE TYPE reviewstatus AS ENUM ('open', 'resolved')")
    op.execute("CREATE TYPE reviewresolution AS ENUM ('approve', 'reject')")

    # Agreements table
    op.create_table(
        'agreements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('public_id', sa.String(12), unique=True, nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('proof_type', postgresql.ENUM('url', 'file', name='prooftype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'draft', 'awaiting_funding', 'funded', 'proof_submitted',
            'validating', 'passed', 'failed', 'manual_review_required',
            'paid', 'expired', 'cancelled',
            name='agreementstatus', create_type=False
        ), nullable=False, server_default='draft'),
        sa.Column('payer_email', sa.String(255), nullable=True),
        sa.Column('payee_email', sa.String(255), nullable=True),
        sa.Column('funding_url_token', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('submit_url_token', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Validation configs table
    op.create_table(
        'validation_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('config_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('stripe_payment_intent_id', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('status', postgresql.ENUM(
            'pending', 'authorized', 'captured', 'failed', 'cancelled', 'refunded',
            name='paymentstatus', create_type=False
        ), nullable=False, server_default='pending'),
        sa.Column('funded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Submissions table
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('proof_type', postgresql.ENUM('url', 'file', name='prooftype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'submitted', 'validating', 'passed', 'failed', 'manual_review_required',
            name='submissionstatus', create_type=False
        ), nullable=False, server_default='submitted'),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(512), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_submissions_agreement', 'submissions', ['agreement_id'])

    # Validation results table
    op.create_table(
        'validation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('validator_type', sa.String(50), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Numeric(5, 2), nullable=True),
        sa.Column('details_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_validation_results_submission', 'validation_results', ['submission_id'])

    # Decision logs table
    op.create_table(
        'decision_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision_type', postgresql.ENUM(
            'authorize_payment', 'reject_submission', 'request_manual_review', 'capture_payment',
            name='decisiontype', create_type=False
        ), nullable=False),
        sa.Column('outcome', postgresql.ENUM(
            'approved', 'rejected', 'manual_review', 'error',
            name='decisionoutcome', create_type=False
        ), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_decision_logs_agreement', 'decision_logs', ['agreement_id'])
    op.create_index('idx_decision_logs_created', 'decision_logs', ['created_at'])

    # Reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('open', 'resolved', name='reviewstatus', create_type=False), nullable=False, server_default='open'),
        sa.Column('resolution', postgresql.ENUM('approve', 'reject', name='reviewresolution', create_type=False), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_reviews_status', 'reviews', ['status'])

    # File objects table
    op.create_table(
        'file_objects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agreement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agreements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('object_key', sa.String(512), unique=True, nullable=False, index=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('file_objects')
    op.drop_table('reviews')
    op.drop_table('decision_logs')
    op.drop_table('validation_results')
    op.drop_table('submissions')
    op.drop_table('payments')
    op.drop_table('validation_configs')
    op.drop_table('agreements')

    op.execute('DROP TYPE reviewresolution')
    op.execute('DROP TYPE reviewstatus')
    op.execute('DROP TYPE decisionoutcome')
    op.execute('DROP TYPE decisiontype')
    op.execute('DROP TYPE submissionstatus')
    op.execute('DROP TYPE paymentstatus')
    op.execute('DROP TYPE agreementstatus')
    op.execute('DROP TYPE prooftype')
