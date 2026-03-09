"""baseline schema with core tables

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260308_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_strategies_owner_id", "strategies", ["owner_id"])

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("rule", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("endpoint", sa.String(length=256), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_idempotency_records_actor_id", "idempotency_records", ["actor_id"])
    op.create_index("ix_idempotency_records_idempotency_key", "idempotency_records", ["idempotency_key"])
    op.create_index("ix_idempotency_records_endpoint", "idempotency_records", ["endpoint"])

    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scan_jobs_timeframe", "scan_jobs", ["timeframe"])
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_scan_jobs_status", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_timeframe", table_name="scan_jobs")
    op.drop_table("scan_jobs")

    op.drop_index("ix_idempotency_records_endpoint", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_idempotency_key", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_actor_id", table_name="idempotency_records")
    op.drop_table("idempotency_records")

    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_alerts_user_id", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index("ix_strategies_owner_id", table_name="strategies")
    op.drop_table("strategies")
