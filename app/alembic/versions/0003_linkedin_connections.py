"""linkedin_connections — per-client LinkedIn Ads OAuth state

Revision ID: 0003_linkedin_connections
Revises: 0002_audits_actions
Create Date: 2026-05-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_linkedin_connections"
down_revision: str | None = "0002_audits_actions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "linkedin_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("linkedin_member_urn", sa.String(128), nullable=False),
        sa.Column("linkedin_member_name", sa.String(255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("ad_accounts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="connected"),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "connected_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.UniqueConstraint(
            "client_id",
            "linkedin_member_urn",
            name="uq_linkedin_client_member",
        ),
    )
    op.create_index(
        "ix_linkedin_connections_client_id",
        "linkedin_connections",
        ["client_id"],
    )
    op.create_index(
        "ix_linkedin_connections_status_expires",
        "linkedin_connections",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_linkedin_connections_status_expires", table_name="linkedin_connections")
    op.drop_index("ix_linkedin_connections_client_id", table_name="linkedin_connections")
    op.drop_table("linkedin_connections")
