"""Fixtures dos testes da API.

O teste da API usa um SQLite em memória criado com create_all: é um banco descartável só para os testes
(o guia da disciplina aceita). O banco de verdade continua vindo das migrações, que são testadas contra
PostgreSQL em tests/test_migracoes.py.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infraestrutura.db import Base, obter_sessao
from app.infraestrutura.modelos import LeituraModelo, RegiaoModelo
from main import app


@pytest.fixture()
def cliente():
    motor = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(motor, "connect")
    def _liga_chaves_estrangeiras(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(motor)
    Sessao = sessionmaker(bind=motor, expire_on_commit=False)
    with Sessao() as s:   # dados de teste: duas regiões, uma com leituras
        s.add_all([
            RegiaoModelo(id="jardim-helena", nome="Jardim Helena", corrego="Córrego Itaim",
                         cota_alerta_cm=80, cota_emergencia_cm=120),
            RegiaoModelo(id="itaim-paulista", nome="Itaim Paulista", corrego="Rio Itaquera",
                         cota_alerta_cm=90, cota_emergencia_cm=130),
        ])
        base = datetime(2026, 11, 15, 17, 30, tzinfo=timezone.utc)
        s.add_all([LeituraModelo(regiao_id="jardim-helena", momento=base - timedelta(hours=h), nivel_cm=n,
                                 risco=r) for h, n, r in [(2, 70, "verde"), (1, 84, "amarelo"), (0, 92, "amarelo")]])
        s.commit()

    def _sessao_de_teste():
        with Sessao() as s:
            yield s

    app.dependency_overrides[obter_sessao] = _sessao_de_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    motor.dispose()
