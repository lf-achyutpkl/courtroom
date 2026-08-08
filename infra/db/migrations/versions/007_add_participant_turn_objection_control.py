from pathlib import Path

from alembic import op


revision = "007_objection_control"
down_revision = "006_interactive_trial_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    path = Path(__file__).resolve().parents[1] / "007_add_participant_turn_objection_control.sql"
    op.execute(path.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.drop_column("participant_turns", "object_requested")
