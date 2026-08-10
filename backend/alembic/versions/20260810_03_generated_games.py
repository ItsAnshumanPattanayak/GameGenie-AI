"""Create persistent generated games.

Revision ID: 20260810_03
Revises: 20260810_02
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_03"
down_revision: str | None = "20260810_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generated_games",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=60), nullable=False),
        sa.Column("prompt", sa.String(length=2000), nullable=False),
        sa.Column("template_type", sa.String(length=32), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("config_version", sa.String(length=16), nullable=False),
        sa.Column("public_slug", sa.String(length=64), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_generated_games_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_games")),
    )
    op.create_index(op.f("ix_generated_games_public_slug"), "generated_games", ["public_slug"], unique=True)
    op.create_index(op.f("ix_generated_games_template_type"), "generated_games", ["template_type"], unique=False)
    op.create_index(op.f("ix_generated_games_user_id"), "generated_games", ["user_id"], unique=False)
    op.create_index("ix_generated_games_user_created", "generated_games", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generated_games_user_created", table_name="generated_games")
    op.drop_index(op.f("ix_generated_games_user_id"), table_name="generated_games")
    op.drop_index(op.f("ix_generated_games_template_type"), table_name="generated_games")
    op.drop_index(op.f("ix_generated_games_public_slug"), table_name="generated_games")
    op.drop_table("generated_games")
