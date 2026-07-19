from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "003_add_simulation_audio_stage"
down_revision = "002_create_simulation_runs"
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("003_add_simulation_audio_stage.sql"))


def downgrade() -> None:
    op.drop_column("simulation_runs", "audio_storage")
    op.drop_column("simulation_runs", "audio_manifest")
    op.execute(
        """
        ALTER TABLE simulation_runs
            DROP CONSTRAINT IF EXISTS chk_simulation_runs_status;

        ALTER TABLE simulation_runs
            ADD CONSTRAINT chk_simulation_runs_status CHECK (
                status IN ('pending', 'running', 'completed', 'failed')
            );
        """
    )
