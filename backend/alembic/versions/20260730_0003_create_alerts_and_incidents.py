"""create alerts and incidents tables"""

from alembic import op
import sqlalchemy as sa

revision = "20260730_0003"
down_revision = "20260730_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("endpoint_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("correlation_key", sa.String(length=120), nullable=False),
        sa.Column("first_event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_alert_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], name=op.f("fk_incidents_endpoint_id_endpoints")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
    )
    op.create_index(op.f("ix_incidents_endpoint_id"), "incidents", ["endpoint_id"], unique=False)
    op.create_index(op.f("ix_incidents_correlation_key"), "incidents", ["correlation_key"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("raw_event_id", sa.String(length=36), nullable=False),
        sa.Column("endpoint_id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("rule_name", sa.String(length=100), nullable=False),
        sa.Column("correlation_key", sa.String(length=120), nullable=False),
        sa.Column("mitre_technique", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], name=op.f("fk_alerts_endpoint_id_endpoints")),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_alerts_incident_id_incidents")),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_alerts_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.UniqueConstraint("raw_event_id", name=op.f("uq_alerts_raw_event_id")),
    )
    op.create_index(op.f("ix_alerts_endpoint_id"), "alerts", ["endpoint_id"], unique=False)
    op.create_index(op.f("ix_alerts_incident_id"), "alerts", ["incident_id"], unique=False)
    op.create_index(op.f("ix_alerts_correlation_key"), "alerts", ["correlation_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_correlation_key"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_incident_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_endpoint_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_incidents_correlation_key"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_endpoint_id"), table_name="incidents")
    op.drop_table("incidents")
