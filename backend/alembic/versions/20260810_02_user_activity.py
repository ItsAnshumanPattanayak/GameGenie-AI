"""Create search history, favourites, and recommendation feedback.

Revision ID: 20260810_02
Revises: 20260810_01
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_02"
down_revision: str | None = "20260810_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("query", sa.String(length=2000), nullable=False),
        sa.Column("extracted_preferences", sa.JSON(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("processing_time_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_search_history_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_history")),
    )
    op.create_index(op.f("ix_search_history_user_id"), "search_history", ["user_id"], unique=False)
    op.create_index("ix_search_history_user_created", "search_history", ["user_id", "created_at"], unique=False)

    op.create_table(
        "favourite_games",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_favourite_games_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favourite_games")),
        sa.UniqueConstraint("user_id", "game_id", name="uq_favourite_games_user_game"),
    )
    op.create_index(op.f("ix_favourite_games_game_id"), "favourite_games", ["game_id"], unique=False)
    op.create_index(op.f("ix_favourite_games_user_id"), "favourite_games", ["user_id"], unique=False)
    op.create_index("ix_favourite_games_user_created", "favourite_games", ["user_id", "created_at"], unique=False)

    op.create_table(
        "recommendation_feedback",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=128), nullable=False),
        sa.Column("search_id", sa.String(length=36), nullable=True),
        sa.Column("feedback_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["search_id"],
            ["search_history.id"],
            name=op.f("fk_recommendation_feedback_search_id_search_history"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_recommendation_feedback_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendation_feedback")),
    )
    op.create_index(op.f("ix_recommendation_feedback_game_id"), "recommendation_feedback", ["game_id"], unique=False)
    op.create_index(
        op.f("ix_recommendation_feedback_search_id"), "recommendation_feedback", ["search_id"], unique=False
    )
    op.create_index(op.f("ix_recommendation_feedback_user_id"), "recommendation_feedback", ["user_id"], unique=False)
    op.create_index(
        "ix_recommendation_feedback_user_created",
        "recommendation_feedback",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_feedback_user_game",
        "recommendation_feedback",
        ["user_id", "game_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_feedback_user_game", table_name="recommendation_feedback")
    op.drop_index("ix_recommendation_feedback_user_created", table_name="recommendation_feedback")
    op.drop_index(op.f("ix_recommendation_feedback_user_id"), table_name="recommendation_feedback")
    op.drop_index(op.f("ix_recommendation_feedback_search_id"), table_name="recommendation_feedback")
    op.drop_index(op.f("ix_recommendation_feedback_game_id"), table_name="recommendation_feedback")
    op.drop_table("recommendation_feedback")
    op.drop_index("ix_favourite_games_user_created", table_name="favourite_games")
    op.drop_index(op.f("ix_favourite_games_user_id"), table_name="favourite_games")
    op.drop_index(op.f("ix_favourite_games_game_id"), table_name="favourite_games")
    op.drop_table("favourite_games")
    op.drop_index("ix_search_history_user_created", table_name="search_history")
    op.drop_index(op.f("ix_search_history_user_id"), table_name="search_history")
    op.drop_table("search_history")
