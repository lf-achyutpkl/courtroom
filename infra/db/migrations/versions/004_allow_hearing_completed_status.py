from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "004_allow_hearing_completed_status"
down_revision = "003_add_simulation_audio_stage"
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("004_allow_hearing_completed_status.sql"))


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE simulation_runs
            DROP CONSTRAINT IF EXISTS chk_simulation_runs_status;

        ALTER TABLE simulation_runs
            ADD CONSTRAINT chk_simulation_runs_status CHECK (
                status IN (
                    'pending',
                    'running',
                    'generating_audio',
                    'completed',
                    'failed'
                )
            );
        """
    )
