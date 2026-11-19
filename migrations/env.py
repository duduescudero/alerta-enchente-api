from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.infraestrutura import modelos  # noqa: F401  (registra as tabelas no metadata)
from app.infraestrutura.db import Base, url_do_banco

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=url_do_banco(), target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    motor = create_engine(url_do_banco(), poolclass=pool.NullPool)
    with motor.connect() as conexao:
        context.configure(connection=conexao, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
