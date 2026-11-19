"""Acesso a dados: toda consulta ao banco mora aqui, longe do domínio e das rotas."""
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.dominio.regiao import Regiao
from app.infraestrutura.modelos import LeituraModelo, OcorrenciaModelo, RegiaoModelo


def regiao_do_modelo(m: RegiaoModelo) -> Regiao:
    return Regiao(id=m.id, nome=m.nome, corrego=m.corrego,
                  cota_alerta_cm=m.cota_alerta_cm, cota_emergencia_cm=m.cota_emergencia_cm)


class RegiaoRepositorio:
    def __init__(self, sessao: Session):
        self.sessao = sessao

    def obter(self, regiao_id: str) -> RegiaoModelo | None:
        return self.sessao.get(RegiaoModelo, regiao_id)

    def adicionar(self, regiao: Regiao) -> RegiaoModelo:
        modelo = RegiaoModelo(id=regiao.id, nome=regiao.nome, corrego=regiao.corrego,
                              cota_alerta_cm=regiao.cota_alerta_cm, cota_emergencia_cm=regiao.cota_emergencia_cm)
        self.sessao.add(modelo)
        return modelo

    def atualizar(self, modelo: RegiaoModelo, regiao: Regiao) -> RegiaoModelo:
        modelo.nome, modelo.corrego = regiao.nome, regiao.corrego
        modelo.cota_alerta_cm, modelo.cota_emergencia_cm = regiao.cota_alerta_cm, regiao.cota_emergencia_cm
        return modelo

    def remover(self, modelo: RegiaoModelo) -> None:
        self.sessao.delete(modelo)

    def listar_com_ultima_leitura(self) -> list[tuple[RegiaoModelo, LeituraModelo | None]]:
        """Cada região com a leitura mais recente do córrego (o que o app mostra na tela inicial)."""
        ultima = (select(LeituraModelo.regiao_id, func.max(LeituraModelo.momento).label("momento"))
                  .group_by(LeituraModelo.regiao_id).subquery())
        consulta = (select(RegiaoModelo, LeituraModelo)
                    .outerjoin(ultima, ultima.c.regiao_id == RegiaoModelo.id)
                    .outerjoin(LeituraModelo, and_(LeituraModelo.regiao_id == RegiaoModelo.id,
                                                   LeituraModelo.momento == ultima.c.momento))
                    .order_by(RegiaoModelo.nome, LeituraModelo.id.desc()))
        vistas, resultado = set(), []
        for regiao, leitura in self.sessao.execute(consulta).all():
            if regiao.id not in vistas:      # empate no mesmo instante: fica a última gravada
                vistas.add(regiao.id)
                resultado.append((regiao, leitura))
        return resultado

    def ultima_leitura(self, regiao_id: str) -> LeituraModelo | None:
        consulta = (select(LeituraModelo).where(LeituraModelo.regiao_id == regiao_id)
                    .order_by(LeituraModelo.momento.desc(), LeituraModelo.id.desc()).limit(1))
        return self.sessao.scalars(consulta).first()


class LeituraRepositorio:
    def __init__(self, sessao: Session):
        self.sessao = sessao

    def adicionar(self, regiao_id: str, momento: datetime, nivel_cm: int, risco: str) -> LeituraModelo:
        modelo = LeituraModelo(regiao_id=regiao_id, momento=momento, nivel_cm=nivel_cm, risco=risco)
        self.sessao.add(modelo)
        return modelo

    def listar_periodo(self, regiao_id: str, de: datetime | None, ate: datetime | None,
                       limite: int) -> list[LeituraModelo]:
        """Leituras de uma região num período, da mais recente para a mais antiga."""
        consulta = select(LeituraModelo).where(LeituraModelo.regiao_id == regiao_id)
        if de:
            consulta = consulta.where(LeituraModelo.momento >= de)
        if ate:
            consulta = consulta.where(LeituraModelo.momento <= ate)
        consulta = consulta.order_by(LeituraModelo.momento.desc(), LeituraModelo.id.desc()).limit(limite)
        return list(self.sessao.scalars(consulta))


class OcorrenciaRepositorio:
    def __init__(self, sessao: Session):
        self.sessao = sessao

    def obter(self, ocorrencia_id: int) -> OcorrenciaModelo | None:
        return self.sessao.get(OcorrenciaModelo, ocorrencia_id)

    def adicionar(self, modelo: OcorrenciaModelo) -> OcorrenciaModelo:
        self.sessao.add(modelo)
        return modelo

    def existe_para_regiao(self, regiao_id: str) -> bool:
        consulta = select(OcorrenciaModelo.id).where(OcorrenciaModelo.regiao_id == regiao_id).limit(1)
        return self.sessao.scalars(consulta).first() is not None

    def buscar(self, regiao_id: str | None, status: str | None, pagina: int,
               tamanho: int) -> tuple[list[OcorrenciaModelo], int]:
        """Filtro por região e status, mais recentes primeiro, com paginação."""
        filtros = []
        if regiao_id:
            filtros.append(OcorrenciaModelo.regiao_id == regiao_id)
        if status:
            filtros.append(OcorrenciaModelo.status == status)
        total = self.sessao.scalar(select(func.count()).select_from(OcorrenciaModelo).where(*filtros))
        consulta = (select(OcorrenciaModelo).where(*filtros)
                    .order_by(OcorrenciaModelo.criado_em.desc(), OcorrenciaModelo.id.desc())
                    .offset((pagina - 1) * tamanho).limit(tamanho))
        return list(self.sessao.scalars(consulta)), int(total or 0)
