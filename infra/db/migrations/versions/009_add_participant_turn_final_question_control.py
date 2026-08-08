"""Add final-question control to participant turns."""

from pathlib import Path

from alembic import op

revision = "009_final_question_control"
down_revision = "008_human_witness_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "009_add_participant_turn_final_question_control.sql"
    )
    op.execute(path.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.drop_column("participant_turns", "is_final")
