"""DTOs: o formato que entra e sai pela API (camelCase, igual ao app de Mobile).

O DTO valida o formato; a entidade do domínio valida a regra.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.dominio.ocorrencia import StatusOcorrencia, TipoOcorrencia
from app.dominio.regiao import NivelDeRisco


class Esquema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class DetalheDoErro(Esquema):
    campo: str = Field(examples=["cotaEmergenciaCm"])
    problema: str = Field(examples=["Field required"])


class Erro(Esquema):
    erro: str = Field(examples=["região 'vila-nova' não encontrada"])
    detalhes: list[DetalheDoErro] | None = Field(default=None, description="Campos inválidos, quando houver")


# ---------- Regiões ----------
class RegiaoEntrada(Esquema):
    id: str | None = Field(default=None, max_length=60, description="Opcional: se faltar, é gerado a partir do nome",
                           examples=["jardim-romano"])
    nome: str = Field(min_length=3, max_length=120, examples=["Jardim Romano"])
    corrego: str = Field(min_length=3, max_length=120, examples=["Córrego Três Pontes"])
    cota_alerta_cm: int = Field(gt=0, le=2000, examples=[80])
    cota_emergencia_cm: int = Field(gt=0, le=2000, description="Precisa ser maior que a cota de alerta",
                                    examples=[120])


class RegiaoAtualizacao(Esquema):
    nome: str = Field(min_length=3, max_length=120, examples=["Jardim Helena"])
    corrego: str = Field(min_length=3, max_length=120, examples=["Córrego Itaim"])
    cota_alerta_cm: int = Field(gt=0, le=2000, examples=[75])
    cota_emergencia_cm: int = Field(gt=0, le=2000, examples=[115])


class RegiaoSaida(Esquema):
    """Mesmo contrato do app de Mobile (src/types.ts), mais o farol calculado pelo backend."""
    id: str = Field(examples=["jardim-helena"])
    nome: str = Field(examples=["Jardim Helena"])
    corrego: str = Field(examples=["Córrego Itaim"])
    nivel_cm: int = Field(description="Última leitura do sensor do córrego", examples=[92])
    cota_alerta_cm: int = Field(examples=[80])
    cota_emergencia_cm: int = Field(examples=[120])
    atualizado_em: datetime = Field(examples=["2026-11-15T17:30:00Z"])
    risco: NivelDeRisco = Field(examples=["amarelo"])
    orientacao: str = Field(examples=["Fique atento. Guarde documentos e remédios em lugar alto e evite atravessar ruas alagadas."])


# ---------- Leituras ----------
class LeituraEntrada(Esquema):
    nivel_cm: int = Field(description="Nível do córrego em cm (0 a 2000). -999 indica falha do sensor e é recusado",
                          examples=[134])
    momento: datetime | None = Field(default=None, description="Quando a medição foi feita (padrão: agora)",
                                     examples=["2026-11-19T18:00:00-03:00"])


class LeituraSaida(Esquema):
    id: int = Field(examples=[13])
    regiao_id: str = Field(examples=["itaim-paulista"])
    momento: datetime = Field(examples=["2026-11-19T21:00:00Z"])
    nivel_cm: int = Field(examples=[134])
    risco: NivelDeRisco = Field(examples=["vermelho"])


# ---------- Ocorrências ----------
class OcorrenciaEntrada(Esquema):
    regiao_id: str = Field(examples=["jardim-helena"])
    tipo: TipoOcorrencia = Field(examples=["bueiro_entupido"])
    local: str = Field(max_length=200, description="Rua ou ponto de referência", examples=["Rua Três Pontes, perto da escola"])
    descricao: str | None = Field(default=None, max_length=500, examples=["Água subindo na calçada desde as 17h"])


class OcorrenciaSaida(Esquema):
    id: int = Field(examples=[1])
    regiao_id: str = Field(examples=["jardim-helena"])
    tipo: TipoOcorrencia = Field(examples=["bueiro_entupido"])
    local: str = Field(examples=["Rua Três Pontes, perto da escola"])
    descricao: str = Field(examples=["Água subindo na calçada desde as 17h"])
    status: StatusOcorrencia = Field(examples=["aberta"])
    criado_em: datetime = Field(examples=["2026-11-19T20:05:00Z"])
    atualizado_em: datetime = Field(examples=["2026-11-19T20:05:00Z"])


class MudancaDeStatus(Esquema):
    status: StatusOcorrencia = Field(examples=["em_atendimento"])


class PaginaDeOcorrencias(Esquema):
    itens: list[OcorrenciaSaida]
    total: int = Field(examples=[1])
    pagina: int = Field(examples=[1])
    tamanho: int = Field(examples=[20])
