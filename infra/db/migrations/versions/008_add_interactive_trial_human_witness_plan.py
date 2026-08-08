"""Persist ordered human witness plans for interactive trials."""

from pathlib import Path

from alembic import op

revision = "008_human_witness_plan"
down_revision = "007_objection_control"
branch_labels = None
depends_on = None


def upgrade() -> None:
    path = Path(__file__).resolve().parents[1] / "008_add_interactive_trial_human_witness_plan.sql"
    op.execute(path.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.drop_column("interactive_trial_runs", "human_witness_plan")
