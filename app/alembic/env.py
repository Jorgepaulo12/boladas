from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from models import Base  # Certifique-se de que o 'Base' é importado corretamente

# Este é o objeto de configuração do Alembic
config = context.config

# Carregar o arquivo de configuração de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados das suas tabelas para suporte ao autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Executa as migrações no modo offline.

    Isso configura o contexto apenas com uma URL, sem criar o Engine.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Executa as migrações no modo online.

    Neste cenário, precisamos criar um Engine e associar uma conexão ao contexto.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# Verifica se está rodando em modo offline ou online e executa a função correta
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


