from pathlib import Path

from alembic import op

revision = "006_interactive_trial_runs"
down_revision = "005_create_case_file_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    path = Path(__file__).resolve().parents[1] / "006_create_interactive_trial_runs.sql"
    op.execute(path.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.drop_table("participant_turns")
    op.drop_table("interactive_trial_runs")
