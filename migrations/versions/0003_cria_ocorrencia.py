"""evolução do esquema: ocorrências registradas pelos moradores no app

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ocorrencia",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("regiao_id", sa.String(60), sa.ForeignKey("regiao.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("local", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="aberta"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tipo IN ('rua_alagada', 'corrego_subindo', 'bueiro_entupido', 'entulho')",
                           name="ck_ocorrencia_tipo"),
        sa.CheckConstraint("status IN ('aberta', 'em_atendimento', 'resolvida')", name="ck_ocorrencia_status"),
    )
    op.create_index("ix_ocorrencia_regiao_status", "ocorrencia", ["regiao_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ocorrencia_regiao_status", table_name="ocorrencia")
    op.drop_table("ocorrencia")
