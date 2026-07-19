from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "001_create_case_files"
down_revision = None
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("001_create_case_files.sql"))


def downgrade() -> None:
    op.drop_index("idx_case_files_created_at", table_name="case_files")
    op.drop_index("idx_case_files_case_type", table_name="case_files")
    op.drop_index("idx_case_files_case_id", table_name="case_files")
    op.drop_table("case_files")
