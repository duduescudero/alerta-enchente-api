"""cria as tabelas regiao e leitura

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regiao",
        sa.Column("id", sa.String(60), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("corrego", sa.String(120), nullable=False),
        sa.Column("cota_alerta_cm", sa.Integer(), nullable=False),
        sa.Column("cota_emergencia_cm", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cota_emergencia_cm > cota_alerta_cm", name="ck_regiao_cotas"),
    )
    op.create_table(
        "leitura",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("regiao_id", sa.String(60), sa.ForeignKey("regiao.id", ondelete="CASCADE"), nullable=False),
        sa.Column("momento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("nivel_cm", sa.Integer(), nullable=False),
        sa.Column("risco", sa.String(10), nullable=False),
        sa.CheckConstraint("nivel_cm BETWEEN 0 AND 2000", name="ck_leitura_nivel"),
    )
    op.create_index("ix_leitura_regiao_momento", "leitura", ["regiao_id", "momento"])


def downgrade() -> None:
    op.drop_index("ix_leitura_regiao_momento", table_name="leitura")
    op.drop_table("leitura")
    op.drop_table("regiao")
