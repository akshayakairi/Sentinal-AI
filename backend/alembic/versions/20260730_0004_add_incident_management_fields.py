"""add incident management fields and notes table"""

from alembic import op
import sqlalchemy as sa

revision = "20260730_0004"
down_revision = "20260730_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("assigned_to_user_id", sa.String(length=36), nullable=True))
    op.add_column("incidents", sa.Column("resolution_summary", sa.Text(), nullable=True))
    op.create_index(op.f("ix_incidents_assigned_to_user_id"), "incidents", ["assigned_to_user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_incidents_assigned_to_user_id_users"),
        "incidents",
        "users",
        ["assigned_to_user_id"],
        ["id"],
    )

    op.create_table(
        "incident_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], name=op.f("fk_incident_notes_author_user_id_users")),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_incident_notes_incident_id_incidents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_notes")),
    )
    op.create_index(op.f("ix_incident_notes_author_user_id"), "incident_notes", ["author_user_id"], unique=False)
    op.create_index(op.f("ix_incident_notes_incident_id"), "incident_notes", ["incident_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_notes_incident_id"), table_name="incident_notes")
    op.drop_index(op.f("ix_incident_notes_author_user_id"), table_name="incident_notes")
    op.drop_table("incident_notes")
    op.drop_constraint(op.f("fk_incidents_assigned_to_user_id_users"), "incidents", type_="foreignkey")
    op.drop_index(op.f("ix_incidents_assigned_to_user_id"), table_name="incidents")
    op.drop_column("incidents", "resolution_summary")
    op.drop_column("incidents", "assigned_to_user_id")
