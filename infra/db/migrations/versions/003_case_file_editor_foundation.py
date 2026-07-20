from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "003_case_file_editor_foundation"
down_revision = "004_allow_hearing_completed"
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("003_case_file_editor_foundation.sql"))


def downgrade() -> None:
    op.drop_column("case_files", "updated_at")
    op.drop_column("case_files", "revision")
    op.drop_column("case_files", "status")
    op.drop_column("case_files", "case_title")
    op.alter_column("case_files", "case_json", new_column_name="case_file")
