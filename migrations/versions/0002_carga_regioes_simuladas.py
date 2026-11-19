"""carga das 4 regiões do Jardim Helena e arredores, com leituras SIMULADAS do sensor

As regiões e as cotas são as mesmas do app de Mobile (src/mock/regioes.json).
Os níveis são simulados para demonstração: não são medições reais.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19
"""
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

REGIOES = [
    # id, nome, córrego, cota de alerta, cota de emergência, leituras simuladas (de hora em hora)
    ("jardim-helena", "Jardim Helena", "Córrego Itaim", 80, 120, [61, 70, 84, 92]),
    ("vila-itaim", "Vila Itaim", "Córrego Lajeado", 80, 120, [35, 38, 40, 41]),
    ("itaim-paulista", "Itaim Paulista", "Rio Itaquera", 90, 130, [88, 101, 122, 134]),
    ("sao-miguel", "São Miguel Paulista", "Córrego Água Vermelha", 85, 125, [50, 54, 57, 58]),
]
ULTIMA_LEITURA = datetime(2026, 11, 15, 17, 30, tzinfo=timezone.utc)   # 15/11/2026 14h30 em Brasília


def _risco(nivel: int, alerta: int, emergencia: int) -> str:
    # mesma regra de app.dominio.regiao.Regiao.classificar (conferida em tests/test_migracoes.py)
    return "vermelho" if nivel >= emergencia else "amarelo" if nivel >= alerta else "verde"


def upgrade() -> None:
    regiao = sa.table("regiao", sa.column("id"), sa.column("nome"), sa.column("corrego"),
                      sa.column("cota_alerta_cm"), sa.column("cota_emergencia_cm"))
    leitura = sa.table("leitura", sa.column("regiao_id"), sa.column("momento", sa.DateTime(timezone=True)),
                       sa.column("nivel_cm"), sa.column("risco"))
    op.bulk_insert(regiao, [{"id": i, "nome": n, "corrego": c, "cota_alerta_cm": a, "cota_emergencia_cm": e}
                            for i, n, c, a, e, _ in REGIOES])
    linhas = []
    for i, _, _, a, e, niveis in REGIOES:
        for k, nivel in enumerate(niveis):
            momento = ULTIMA_LEITURA - timedelta(hours=len(niveis) - 1 - k)
            linhas.append({"regiao_id": i, "momento": momento, "nivel_cm": nivel, "risco": _risco(nivel, a, e)})
    op.bulk_insert(leitura, linhas)


def downgrade() -> None:
    ids = ", ".join(f"'{i}'" for i, *_ in REGIOES)
    op.execute(f"DELETE FROM leitura WHERE regiao_id IN ({ids})")
    op.execute(f"DELETE FROM regiao WHERE id IN ({ids})")
