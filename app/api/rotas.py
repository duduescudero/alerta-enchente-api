"""Endpoints REST. Aqui só entra HTTP: as regras ficam no domínio e a orquestração nos casos de uso."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.erros import erros
from app.api.esquemas import (LeituraEntrada, LeituraSaida, MudancaDeStatus, OcorrenciaEntrada,
                              OcorrenciaSaida, PaginaDeOcorrencias, RegiaoAtualizacao, RegiaoEntrada,
                              RegiaoSaida)
from app.aplicacao.casos_de_uso import (LeiturasServico, OcorrenciasServico, RegioesServico,
                                        SituacaoDaRegiao)
from app.dominio.ocorrencia import StatusOcorrencia
from app.infraestrutura.db import obter_sessao

regioes = APIRouter(prefix="/regioes", tags=["Regiões"])
leituras = APIRouter(prefix="/regioes/{regiao_id}/leituras", tags=["Leituras do sensor"])
ocorrencias = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])
sistema = APIRouter(tags=["Sistema"])


def _saida(s: SituacaoDaRegiao) -> RegiaoSaida:
    r = s.regiao
    return RegiaoSaida(id=r.id, nome=r.nome, corrego=r.corrego, nivel_cm=s.nivel_cm,
                       cota_alerta_cm=r.cota_alerta_cm, cota_emergencia_cm=r.cota_emergencia_cm,
                       atualizado_em=s.atualizado_em, risco=s.risco, orientacao=s.orientacao)


# ---------------- Regiões (CRUD) ----------------
@regioes.get("", response_model=list[RegiaoSaida], summary="Listar regiões com o farol atual",
             description="Cada região com o último nível do córrego, o farol (verde/amarelo/vermelho) e a orientação "
                         "ao morador. É o endpoint que o app de Mobile consome na tela inicial.")
def listar_regioes(sessao: Session = Depends(obter_sessao)):
    return [_saida(s) for s in RegioesServico(sessao).listar()]


@regioes.get("/{regiao_id}", response_model=RegiaoSaida, summary="Detalhar uma região", responses=erros(404))
def obter_regiao(regiao_id: str, sessao: Session = Depends(obter_sessao)):
    return _saida(RegioesServico(sessao).obter(regiao_id))


@regioes.post("", response_model=RegiaoSaida, status_code=status.HTTP_201_CREATED, response_description="Criado",
              summary="Cadastrar uma região monitorada", responses=erros(409, 422),
              description="A cota de emergência precisa ser maior que a de alerta (regra do domínio → 422). "
                          "Id repetido → 409.")
def criar_regiao(dados: RegiaoEntrada, response: Response, sessao: Session = Depends(obter_sessao)):
    criada = RegioesServico(sessao).criar(dados.nome, dados.corrego, dados.cota_alerta_cm,
                                         dados.cota_emergencia_cm, dados.id)
    response.headers["Location"] = f"/regioes/{criada.regiao.id}"
    return _saida(criada)


@regioes.put("/{regiao_id}", response_model=RegiaoSaida, summary="Atualizar nome, córrego e cotas",
             responses=erros(404, 422))
def atualizar_regiao(regiao_id: str, dados: RegiaoAtualizacao, sessao: Session = Depends(obter_sessao)):
    return _saida(RegioesServico(sessao).atualizar(regiao_id, dados.nome, dados.corrego,
                                                    dados.cota_alerta_cm, dados.cota_emergencia_cm))


@regioes.delete("/{regiao_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Apagar uma região", response_description="Apagada",
                responses=erros(404, 409),
                description="Apaga a região e as leituras dela. Se moradores já registraram ocorrências ali, "
                            "a região não pode ser apagada (409).")
def remover_regiao(regiao_id: str, sessao: Session = Depends(obter_sessao)):
    RegioesServico(sessao).remover(regiao_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------- Leituras do sensor ----------------
@leituras.post("", response_model=LeituraSaida, status_code=status.HTTP_201_CREATED, response_description="Criado",
               summary="Registrar uma leitura do sensor do córrego", responses=erros(404, 422),
               description="Usado pelo sensor ESP32 (Physical Computing). O backend classifica o risco pela cota da "
                           "região. O código de falha -999 é recusado (422).")
def registrar_leitura(regiao_id: str, dados: LeituraEntrada, sessao: Session = Depends(obter_sessao)):
    return LeiturasServico(sessao).registrar(regiao_id, dados.nivel_cm, dados.momento)


@leituras.get("", response_model=list[LeituraSaida], summary="Histórico de leituras num período",
              responses=erros(404, 422),
              description="Da mais recente para a mais antiga. Filtros opcionais de período e limite.")
def listar_leituras(regiao_id: str,
                    de: datetime | None = Query(None, description="Início do período (ISO 8601)",
                                                examples=["2026-11-15T00:00:00-03:00"]),
                    ate: datetime | None = Query(None, description="Fim do período (ISO 8601)",
                                                 examples=["2026-11-16T00:00:00-03:00"]),
                    limite: int = Query(100, ge=1, le=1000, description="Máximo de leituras"),
                    sessao: Session = Depends(obter_sessao)):
    return LeiturasServico(sessao).listar(regiao_id, de, ate, limite)


# ---------------- Ocorrências dos moradores ----------------
@ocorrencias.post("", response_model=OcorrenciaSaida, status_code=status.HTTP_201_CREATED, response_description="Criado",
                  summary="Registrar uma ocorrência (aviso do morador)", responses=erros(404, 422))
def registrar_ocorrencia(dados: OcorrenciaEntrada, sessao: Session = Depends(obter_sessao)):
    return OcorrenciasServico(sessao).registrar(dados.regiao_id, dados.tipo, dados.local, dados.descricao)


@ocorrencias.get("", response_model=PaginaDeOcorrencias, summary="Buscar ocorrências com filtros e paginação",
                 responses=erros(422))
def buscar_ocorrencias(regiao_id: str | None = Query(None, alias="regiaoId", examples=["jardim-helena"]),
                       status_: StatusOcorrencia | None = Query(None, alias="status"),
                       pagina: int = Query(1, ge=1), tamanho: int = Query(20, ge=1, le=100),
                       sessao: Session = Depends(obter_sessao)):
    itens, total = OcorrenciasServico(sessao).buscar(regiao_id, status_, pagina, tamanho)
    return PaginaDeOcorrencias(itens=itens, total=total, pagina=pagina, tamanho=tamanho)


@ocorrencias.get("/{ocorrencia_id}", response_model=OcorrenciaSaida, summary="Detalhar uma ocorrência",
                 responses=erros(404))
def obter_ocorrencia(ocorrencia_id: int, sessao: Session = Depends(obter_sessao)):
    return OcorrenciasServico(sessao).obter(ocorrencia_id)


@ocorrencias.patch("/{ocorrencia_id}/status", response_model=OcorrenciaSaida,
                   summary="Mudar o status (aberta → em atendimento → resolvida)", responses=erros(404, 422),
                   description="Ocorrência resolvida não reabre; transição inválida → 422.")
def mudar_status_ocorrencia(ocorrencia_id: int, dados: MudancaDeStatus, sessao: Session = Depends(obter_sessao)):
    return OcorrenciasServico(sessao).mudar_status(ocorrencia_id, dados.status)


# ---------------- Sistema ----------------
@sistema.get("/health", summary="Saúde da API e do banco")
def saude(sessao: Session = Depends(obter_sessao)):
    sessao.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "ok"}
