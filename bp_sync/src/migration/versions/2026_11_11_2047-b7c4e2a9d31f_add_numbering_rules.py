"""Add numbering_rules

Revision ID: b7c4e2a9d31f
Revises: d898bd14d54f
Create Date: 2026-11-11 20:47:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7c4e2a9d31f"
down_revision: Union[str, None] = "d898bd14d54f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "numbering_rules",
        sa.Column(
            "id_firm",
            sa.Integer(),
            nullable=False,
            comment="ID фирмы отгрузки (shipping_companies.external_id)",
        ),
        sa.Column(
            "doc_type",
            postgresql.ENUM(
                "invoice",
                "contract",
                name="doc_type_enum",
            ),
            nullable=False,
            comment="Тип документа",
        ),
        sa.Column(
            "prefix",
            sa.String(length=3),
            nullable=False,
            comment="Префикс номера документа",
        ),
        sa.Column(
            "length",
            sa.Integer(),
            server_default=sa.text("6"),
            nullable=False,
            comment="Длина номера после дополнения нулями (6 → 000001)",
        ),
        sa.Column(
            "current_number",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Последний выданный номер (без префикса)",
        ),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Уникальный идентификатор",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата и время создания",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата и время последнего обновления",
        ),
        sa.Column(
            "is_deleted_in_bitrix",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="Удалён в Битрикс",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id_firm",
            "doc_type",
            name="uq_numbering_rules_firm_doc_type",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("numbering_rules")
    op.execute("DROP TYPE IF EXISTS doc_type_enum")
