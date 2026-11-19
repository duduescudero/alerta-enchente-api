"""Testes de unidade das regras do domínio: sem banco e sem HTTP."""
import pytest

from app.dominio.erros import RegraViolada
from app.dominio.ocorrencia import (StatusOcorrencia as S, mudar_status, validar_descricao,
                                    validar_local)
from app.dominio.regiao import ORIENTACAO, NivelDeRisco, Regiao, gerar_identificador, validar_nivel


def regiao(alerta=80, emergencia=120) -> Regiao:
    return Regiao(id="", nome="Jardim Helena", corrego="Córrego Itaim",
                  cota_alerta_cm=alerta, cota_emergencia_cm=emergencia)


@pytest.mark.parametrize("nivel, esperado", [
    (0, NivelDeRisco.VERDE), (79, NivelDeRisco.VERDE),
    (80, NivelDeRisco.AMARELO), (119, NivelDeRisco.AMARELO),
    (120, NivelDeRisco.VERMELHO), (2000, NivelDeRisco.VERMELHO),
])
def test_classifica_o_farol_pelas_cotas_da_regiao(nivel, esperado):
    assert regiao().classificar(nivel) == esperado


def test_orientacao_acompanha_o_farol():
    assert regiao().orientar(134) == ORIENTACAO[NivelDeRisco.VERMELHO]
    assert "199" in regiao().orientar(134)


@pytest.mark.parametrize("alerta, emergencia", [(120, 120), (130, 120)])
def test_recusa_cota_de_emergencia_menor_ou_igual_a_de_alerta(alerta, emergencia):
    with pytest.raises(RegraViolada, match="emergência"):
        regiao(alerta, emergencia)


def test_recusa_cota_de_alerta_zero():
    with pytest.raises(RegraViolada):
        regiao(0, 50)


@pytest.mark.parametrize("nivel", [-999, -1, 2001])
def test_recusa_codigo_de_falha_e_nivel_fora_do_alcance_do_sensor(nivel):
    with pytest.raises(RegraViolada, match="alcance do sensor"):
        validar_nivel(nivel)


def test_gera_o_mesmo_identificador_que_o_app_usa():
    assert gerar_identificador("São Miguel Paulista") == "sao-miguel-paulista"
    assert regiao().id == "jardim-helena"


def test_local_da_ocorrencia_e_obrigatorio_e_normalizado():
    assert validar_local("  Rua   Três Pontes ") == "Rua Três Pontes"
    with pytest.raises(RegraViolada, match="onde"):
        validar_local("  ")


def test_descricao_tem_limite():
    assert validar_descricao(None) == ""
    with pytest.raises(RegraViolada):
        validar_descricao("x" * 501)


@pytest.mark.parametrize("atual, novo", [(S.ABERTA, S.EM_ATENDIMENTO), (S.ABERTA, S.RESOLVIDA),
                                         (S.EM_ATENDIMENTO, S.RESOLVIDA)])
def test_ciclo_de_vida_da_ocorrencia_permitido(atual, novo):
    assert mudar_status(atual, novo) == novo


@pytest.mark.parametrize("atual, novo", [(S.RESOLVIDA, S.ABERTA), (S.RESOLVIDA, S.EM_ATENDIMENTO),
                                         (S.EM_ATENDIMENTO, S.ABERTA), (S.ABERTA, S.ABERTA)])
def test_ocorrencia_resolvida_nao_reabre_e_status_nao_volta(atual, novo):
    with pytest.raises(RegraViolada):
        mudar_status(atual, novo)
