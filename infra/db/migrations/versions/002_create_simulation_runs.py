from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "002_create_simulation_runs"
down_revision = "001_create_case_files"
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("002_create_simulation_runs.sql"))


def downgrade() -> None:
    op.drop_index("idx_simulation_runs_created_at", table_name="simulation_runs")
    op.drop_index("idx_simulation_runs_status", table_name="simulation_runs")
    op.drop_index("idx_simulation_runs_case_file_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")
