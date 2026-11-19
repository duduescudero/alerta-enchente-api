"""Tabelas do banco. O esquema real é criado pelas migrações do Alembic (pasta migrations/)."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestrutura.db import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class RegiaoModelo(Base):
    __tablename__ = "regiao"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    corrego: Mapped[str] = mapped_column(String(120), nullable=False)
    cota_alerta_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    cota_emergencia_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=agora)

    leituras: Mapped[list["LeituraModelo"]] = relationship(
        back_populates="regiao", cascade="all, delete-orphan", passive_deletes=True)


class LeituraModelo(Base):
    __tablename__ = "leitura"
    __table_args__ = (Index("ix_leitura_regiao_momento", "regiao_id", "momento"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    regiao_id: Mapped[str] = mapped_column(ForeignKey("regiao.id", ondelete="CASCADE"), nullable=False)
    momento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    nivel_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    risco: Mapped[str] = mapped_column(String(10), nullable=False)

    regiao: Mapped[RegiaoModelo] = relationship(back_populates="leituras")


class OcorrenciaModelo(Base):
    __tablename__ = "ocorrencia"
    __table_args__ = (Index("ix_ocorrencia_regiao_status", "regiao_id", "status"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    regiao_id: Mapped[str] = mapped_column(ForeignKey("regiao.id", ondelete="RESTRICT"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    local: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aberta")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=agora)
