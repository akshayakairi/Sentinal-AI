"""create endpoints and raw events tables"""

from alembic import op
import sqlalchemy as sa

revision = "20260730_0002"
down_revision = "20260730_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "endpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("operating_system", sa.String(length=100), nullable=False),
        sa.Column("agent_version", sa.String(length=50), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_endpoints")),
        sa.UniqueConstraint("hostname", name=op.f("uq_endpoints_hostname")),
    )
    op.create_index(op.f("ix_endpoints_hostname"), "endpoints", ["hostname"], unique=False)

    op.create_table(
        "raw_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("endpoint_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_category", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("event_name", sa.String(length=255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_summary", sa.Text(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], name=op.f("fk_raw_events_endpoint_id_endpoints")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_events")),
    )
    op.create_index(op.f("ix_raw_events_endpoint_id"), "raw_events", ["endpoint_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_raw_events_endpoint_id"), table_name="raw_events")
    op.drop_table("raw_events")
    op.drop_index(op.f("ix_endpoints_hostname"), table_name="endpoints")
    op.drop_table("endpoints")
