from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "005_create_case_file_messages"
down_revision = "003_case_file_editor_foundation"
branch_labels = None
depends_on = None


def _read_sql(filename: str) -> str:
    return (Path(__file__).resolve().parents[1] / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_read_sql("005_create_case_file_messages.sql"))


def downgrade() -> None:
    op.drop_index("idx_case_file_messages_created_at", table_name="case_file_messages")
    op.drop_index("idx_case_file_messages_case_file_id", table_name="case_file_messages")
    op.drop_table("case_file_messages")
