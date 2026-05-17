"""audits, actions, audit_check_results

Revision ID: 0002_audits_actions
Revises: 0001_initial
Create Date: 2026-05-14

Creation order matters: actions is created BEFORE audit_check_results
so the latter's FK to actions resolves cleanly.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_audits_actions"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade", sa.String(2), nullable=False),
        sa.Column(
            "category_scores",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_audits_client_id", "audits", ["client_id"])
    op.create_index("ix_audits_run_at", "audits", ["run_at"])

    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column(
            "target",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "diff",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("reasoning_md", sa.Text(), nullable=False),
        sa.Column(
            "evidence",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "expected_impact",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("risk_tier", sa.String(4), nullable=False, server_default="L2"),
        sa.Column("status", sa.String(16), nullable=False, server_default="proposed"),
        sa.Column(
            "approver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_result", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_actions_client_id", "actions", ["client_id"])
    op.create_index("ix_actions_status", "actions", ["status"])
    op.create_index("ix_actions_audit_id", "actions", ["audit_id"])

    op.create_table(
        "audit_check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_id", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "evidence",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("suggested_fix_md", sa.Text(), nullable=True),
        sa.Column(
            "draft_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("actions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_acr_audit_id", "audit_check_results", ["audit_id"])


def downgrade() -> None:
    op.drop_index("ix_acr_audit_id", table_name="audit_check_results")
    op.drop_table("audit_check_results")
    op.drop_index("ix_actions_audit_id", table_name="actions")
    op.drop_index("ix_actions_status", table_name="actions")
    op.drop_index("ix_actions_client_id", table_name="actions")
    op.drop_table("actions")
    op.drop_index("ix_audits_run_at", table_name="audits")
    op.drop_index("ix_audits_client_id", table_name="audits")
    op.drop_table("audits")
