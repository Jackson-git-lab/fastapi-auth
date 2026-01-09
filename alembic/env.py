import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ajouter le chemin de l'application
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importez vos modèles ici
from app.models import Base
from app.database import Base as BaseDB

# Charger la configuration
config = context.config

# CORRECTION : Configurer un logging basique au lieu de fileConfig
import logging
logging.basicConfig(level=logging.WARNING)

# Tentative de charger fileConfig uniquement si la section [formatters] existe
try:
    if config.config_file_name:
        fileConfig(config.config_file_name)
except KeyError as e:
    # Si la section manque, on continue sans logging configuré
    print(f"Note: Logging configuration skipped - {e}")

# Définir target_metadata
target_metadata = [Base.metadata, BaseDB.metadata]

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # Utiliser DATABASE_URL de l'environnement si disponible
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()