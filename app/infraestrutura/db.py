"""Conexão com o PostgreSQL. A URL (com a senha) vem do ambiente ou do .env, nunca do código."""
import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


def url_do_banco() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Defina DATABASE_URL (copie .env.example para .env e ajuste a senha).")
    return url


class Base(DeclarativeBase):
    """Base dos modelos de tabela (usada pelo Alembic para comparar o esquema)."""


_engine = None
_fabrica = None


def fabrica_de_sessoes() -> sessionmaker:
    global _engine, _fabrica
    if _fabrica is None:
        _engine = create_engine(url_do_banco(), pool_pre_ping=True)
        _fabrica = sessionmaker(bind=_engine, expire_on_commit=False)
    return _fabrica


def obter_sessao() -> Iterator[Session]:
    """Uma sessão por requisição; o caso de uso decide quando fazer commit."""
    sessao = fabrica_de_sessoes()()
    try:
        yield sessao
    finally:
        sessao.close()
