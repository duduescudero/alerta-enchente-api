"""Casos de uso: orquestram domínio e repositórios, e controlam a transação."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.aplicacao.erros import Conflito, NaoEncontrado
from app.dominio.ocorrencia import (StatusOcorrencia, TipoOcorrencia, mudar_status,
                                    validar_descricao, validar_local)
from app.dominio.regiao import NivelDeRisco, Regiao, validar_nivel
from app.dominio.erros import RegraViolada
from app.infraestrutura.modelos import LeituraModelo, OcorrenciaModelo, RegiaoModelo
from app.infraestrutura.repositorios import (LeituraRepositorio, OcorrenciaRepositorio,
                                             RegiaoRepositorio, regiao_do_modelo)


@dataclass
class SituacaoDaRegiao:
    """O que o app mostra: a região, o nível atual do córrego, o farol e a orientação."""
    regiao: Regiao
    nivel_cm: int
    atualizado_em: datetime
    risco: NivelDeRisco
    orientacao: str


def _situacao(modelo: RegiaoModelo, leitura: LeituraModelo | None) -> SituacaoDaRegiao:
    regiao = regiao_do_modelo(modelo)
    nivel = leitura.nivel_cm if leitura else 0          # região nova, ainda sem leitura do sensor
    momento = leitura.momento if leitura else modelo.criado_em
    return SituacaoDaRegiao(regiao, nivel, momento, regiao.classificar(nivel), regiao.orientar(nivel))


def _utc(momento: datetime | None) -> datetime:
    if momento is None:
        return datetime.now(timezone.utc)
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


class RegioesServico:
    def __init__(self, sessao: Session):
        self.sessao = sessao
        self.repo = RegiaoRepositorio(sessao)

    def _buscar(self, regiao_id: str) -> RegiaoModelo:
        modelo = self.repo.obter(regiao_id)
        if modelo is None:
            raise NaoEncontrado(f"região '{regiao_id}' não encontrada")
        return modelo

    def listar(self) -> list[SituacaoDaRegiao]:
        return [_situacao(r, l) for r, l in self.repo.listar_com_ultima_leitura()]

    def obter(self, regiao_id: str) -> SituacaoDaRegiao:
        modelo = self._buscar(regiao_id)
        return _situacao(modelo, self.repo.ultima_leitura(regiao_id))

    def criar(self, nome: str, corrego: str, cota_alerta_cm: int, cota_emergencia_cm: int,
              regiao_id: str | None = None) -> SituacaoDaRegiao:
        regiao = Regiao(id=regiao_id or nome, nome=nome, corrego=corrego,
                        cota_alerta_cm=cota_alerta_cm, cota_emergencia_cm=cota_emergencia_cm)
        if self.repo.obter(regiao.id):
            raise Conflito(f"já existe uma região com o id '{regiao.id}'")
        modelo = self.repo.adicionar(regiao)
        self.sessao.commit()
        return _situacao(modelo, None)

    def atualizar(self, regiao_id: str, nome: str, corrego: str, cota_alerta_cm: int,
                  cota_emergencia_cm: int) -> SituacaoDaRegiao:
        modelo = self._buscar(regiao_id)
        regiao = Regiao(id=modelo.id, nome=nome, corrego=corrego,
                        cota_alerta_cm=cota_alerta_cm, cota_emergencia_cm=cota_emergencia_cm)
        self.repo.atualizar(modelo, regiao)
        self.sessao.commit()
        return _situacao(modelo, self.repo.ultima_leitura(regiao_id))

    def remover(self, regiao_id: str) -> None:
        modelo = self._buscar(regiao_id)
        if OcorrenciaRepositorio(self.sessao).existe_para_regiao(regiao_id):
            raise Conflito("a região tem ocorrências registradas por moradores e não pode ser apagada")
        self.repo.remover(modelo)
        self.sessao.commit()


class LeiturasServico:
    def __init__(self, sessao: Session):
        self.sessao = sessao
        self.regioes = RegiaoRepositorio(sessao)
        self.repo = LeituraRepositorio(sessao)

    def registrar(self, regiao_id: str, nivel_cm: int, momento: datetime | None = None) -> LeituraModelo:
        """O sensor do córrego (ESP32) envia uma medição; o domínio classifica o risco."""
        modelo = self.regioes.obter(regiao_id)
        if modelo is None:
            raise NaoEncontrado(f"região '{regiao_id}' não encontrada")
        nivel = validar_nivel(nivel_cm)
        risco = regiao_do_modelo(modelo).classificar(nivel)
        leitura = self.repo.adicionar(regiao_id, _utc(momento), nivel, risco.value)
        self.sessao.commit()
        return leitura

    def listar(self, regiao_id: str, de: datetime | None, ate: datetime | None,
               limite: int) -> list[LeituraModelo]:
        if self.regioes.obter(regiao_id) is None:
            raise NaoEncontrado(f"região '{regiao_id}' não encontrada")
        if de and ate and _utc(de) > _utc(ate):
            raise RegraViolada("o início do período ('de') precisa ser antes do fim ('ate')")
        return self.repo.listar_periodo(regiao_id, _utc(de) if de else None, _utc(ate) if ate else None, limite)


class OcorrenciasServico:
    def __init__(self, sessao: Session):
        self.sessao = sessao
        self.repo = OcorrenciaRepositorio(sessao)

    def _buscar(self, ocorrencia_id: int) -> OcorrenciaModelo:
        modelo = self.repo.obter(ocorrencia_id)
        if modelo is None:
            raise NaoEncontrado(f"ocorrência {ocorrencia_id} não encontrada")
        return modelo

    def registrar(self, regiao_id: str, tipo: TipoOcorrencia, local: str, descricao: str | None) -> OcorrenciaModelo:
        if RegiaoRepositorio(self.sessao).obter(regiao_id) is None:
            raise NaoEncontrado(f"região '{regiao_id}' não encontrada")
        agora = datetime.now(timezone.utc)
        modelo = OcorrenciaModelo(regiao_id=regiao_id, tipo=TipoOcorrencia(tipo).value,
                                  local=validar_local(local), descricao=validar_descricao(descricao),
                                  status=StatusOcorrencia.ABERTA.value, criado_em=agora, atualizado_em=agora)
        self.repo.adicionar(modelo)
        self.sessao.commit()
        return modelo

    def obter(self, ocorrencia_id: int) -> OcorrenciaModelo:
        return self._buscar(ocorrencia_id)

    def buscar(self, regiao_id: str | None, status: StatusOcorrencia | None, pagina: int, tamanho: int):
        return self.repo.buscar(regiao_id, status.value if status else None, pagina, tamanho)

    def mudar_status(self, ocorrencia_id: int, novo: StatusOcorrencia) -> OcorrenciaModelo:
        modelo = self._buscar(ocorrencia_id)
        modelo.status = mudar_status(StatusOcorrencia(modelo.status), novo).value
        modelo.atualizado_em = datetime.now(timezone.utc)
        self.sessao.commit()
        return modelo
