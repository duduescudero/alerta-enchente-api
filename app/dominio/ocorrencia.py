"""Ocorrência: o aviso que o morador manda pelo app (rua alagada, bueiro entupido...)."""
from enum import Enum

from app.dominio.erros import RegraViolada


class TipoOcorrencia(str, Enum):
    RUA_ALAGADA = "rua_alagada"
    CORREGO_SUBINDO = "corrego_subindo"
    BUEIRO_ENTUPIDO = "bueiro_entupido"
    ENTULHO = "entulho"


class StatusOcorrencia(str, Enum):
    ABERTA = "aberta"
    EM_ATENDIMENTO = "em_atendimento"
    RESOLVIDA = "resolvida"


# Ciclo de vida: a equipe da prefeitura assume e resolve. Ocorrência resolvida não reabre:
# se o problema voltar, o morador registra uma nova (fica o histórico de cada vez).
TRANSICOES_PERMITIDAS = {
    StatusOcorrencia.ABERTA: {StatusOcorrencia.EM_ATENDIMENTO, StatusOcorrencia.RESOLVIDA},
    StatusOcorrencia.EM_ATENDIMENTO: {StatusOcorrencia.RESOLVIDA},
    StatusOcorrencia.RESOLVIDA: set(),
}

LOCAL_MINIMO, LOCAL_MAXIMO, DESCRICAO_MAXIMA = 3, 200, 500


def validar_local(local: str) -> str:
    """Sem um local, a equipe não sabe para onde ir."""
    texto = " ".join((local or "").split())
    if len(texto) < LOCAL_MINIMO:
        raise RegraViolada("diga onde é o problema (rua ou ponto de referência)")
    if len(texto) > LOCAL_MAXIMO:
        raise RegraViolada(f"o local pode ter no máximo {LOCAL_MAXIMO} caracteres")
    return texto


def validar_descricao(descricao: str | None) -> str:
    texto = " ".join((descricao or "").split())
    if len(texto) > DESCRICAO_MAXIMA:
        raise RegraViolada(f"a descrição pode ter no máximo {DESCRICAO_MAXIMA} caracteres")
    return texto


def mudar_status(atual: StatusOcorrencia, novo: StatusOcorrencia) -> StatusOcorrencia:
    """Aplica o ciclo de vida da ocorrência."""
    if novo == atual:
        raise RegraViolada(f"a ocorrência já está com o status '{atual.value}'")
    if novo not in TRANSICOES_PERMITIDAS[atual]:
        raise RegraViolada(f"não é possível passar de '{atual.value}' para '{novo.value}'")
    return novo
