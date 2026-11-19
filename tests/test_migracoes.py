"""Migrações contra um PostgreSQL de verdade: cria o banco do zero, confere a carga e desfaz.

Só roda quando DATABASE_URL_TESTE aponta para um banco DESCARTÁVEL (ele é apagado e recriado).
"""
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.dominio.regiao import Regiao

URL_TESTE = os.getenv("DATABASE_URL_TESTE")
pytestmark = pytest.mark.skipif(not URL_TESTE, reason="defina DATABASE_URL_TESTE para testar as migrações")


@pytest.fixture()
def alembic_no_banco_de_teste(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL_TESTE)
    motor = create_engine(URL_TESTE)
    with motor.begin() as c:   # começa do zero, como o professor ao clonar
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    yield Config("alembic.ini"), motor
    motor.dispose()


def test_migracoes_criam_o_banco_do_zero_e_sao_reversiveis(alembic_no_banco_de_teste):
    cfg, motor = alembic_no_banco_de_teste
    command.upgrade(cfg, "head")
    tabelas = set(inspect(motor).get_table_names())
    assert {"regiao", "leitura", "ocorrencia", "alembic_version"} <= tabelas

    with motor.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == "0003"
        assert c.scalar(text("SELECT count(*) FROM regiao")) == 4
        fks = {fk["referred_table"] for fk in inspect(motor).get_foreign_keys("leitura")}
        assert fks == {"regiao"}
        # a carga simulada respeita a mesma regra do domínio
        for rid, nome, corrego, alerta, emerg, nivel, risco in c.execute(text(
                "SELECT r.id, r.nome, r.corrego, r.cota_alerta_cm, r.cota_emergencia_cm, l.nivel_cm, l.risco "
                "FROM leitura l JOIN regiao r ON r.id = l.regiao_id")):
            assert Regiao(rid, nome, corrego, alerta, emerg).classificar(nivel).value == risco

    command.downgrade(cfg, "base")
    assert set(inspect(motor).get_table_names()) <= {"alembic_version"}
    command.upgrade(cfg, "head")   # e sobe de novo
