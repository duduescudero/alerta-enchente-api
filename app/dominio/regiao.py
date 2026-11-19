"""Região monitorada: o córrego, as cotas e a regra do farol.

Este módulo não conhece HTTP nem banco de dados: só as regras do problema.
"""
from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

from app.dominio.erros import RegraViolada

NIVEL_MINIMO_CM = 0
NIVEL_MAXIMO_CM = 2000   # alcance do sensor ultrassônico do córrego


class NivelDeRisco(str, Enum):
    """O farol que o morador vê no app."""
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"


ORIENTACAO = {
    NivelDeRisco.VERDE: "Sem risco agora. Continue acompanhando em dias de chuva forte.",
    NivelDeRisco.AMARELO: "Fique atento. Guarde documentos e remédios em lugar alto e evite atravessar ruas alagadas.",
    NivelDeRisco.VERMELHO: "Perigo. Saia de áreas baixas, vá para um local seguro e ligue 199 (Defesa Civil) se precisar de ajuda.",
}


def gerar_identificador(nome: str) -> str:
    """'São Miguel Paulista' -> 'sao-miguel-paulista' (o mesmo id que o app usa)."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def validar_nivel(nivel_cm: int) -> int:
    """O transmissor manda -999 quando o sensor falha: isso não é uma leitura."""
    if not NIVEL_MINIMO_CM <= nivel_cm <= NIVEL_MAXIMO_CM:
        raise RegraViolada(
            f"nível fora do alcance do sensor ({NIVEL_MINIMO_CM} a {NIVEL_MAXIMO_CM} cm): {nivel_cm}")
    return nivel_cm


@dataclass(frozen=True)
class Regiao:
    """Bairro monitorado, com as cotas do córrego que passa por ele."""
    id: str
    nome: str
    corrego: str
    cota_alerta_cm: int
    cota_emergencia_cm: int

    def __post_init__(self):
        nome = (self.nome or "").strip()
        corrego = (self.corrego or "").strip()
        if len(nome) < 3:
            raise RegraViolada("o nome da região precisa ter pelo menos 3 letras")
        if len(corrego) < 3:
            raise RegraViolada("informe o córrego ou rio monitorado")
        if self.cota_alerta_cm <= 0:
            raise RegraViolada("a cota de alerta precisa ser maior que zero")
        if self.cota_emergencia_cm <= self.cota_alerta_cm:
            raise RegraViolada("a cota de emergência precisa ser maior que a cota de alerta")
        identificador = gerar_identificador(self.id or nome)
        if not identificador:
            raise RegraViolada("não foi possível gerar o identificador da região")
        object.__setattr__(self, "nome", nome)
        object.__setattr__(self, "corrego", corrego)
        object.__setattr__(self, "id", identificador)

    def classificar(self, nivel_cm: int) -> NivelDeRisco:
        """Mesma regra do app: verde abaixo do alerta, amarelo até a emergência, vermelho daí para cima."""
        validar_nivel(nivel_cm)
        if nivel_cm >= self.cota_emergencia_cm:
            return NivelDeRisco.VERMELHO
        if nivel_cm >= self.cota_alerta_cm:
            return NivelDeRisco.AMARELO
        return NivelDeRisco.VERDE

    def orientar(self, nivel_cm: int) -> str:
        """O que o morador deve fazer agora, em linguagem simples."""
        return ORIENTACAO[self.classificar(nivel_cm)]
