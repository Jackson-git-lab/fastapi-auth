FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ~~SUPPRIMER CETTE LIGNE~~ (alembic est déjà dans requirements.txt)
# RUN pip install alembic psycopg2-binary

# Copier le code
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app

# Port exposé (informative, Render utilise $PORT)
EXPOSE 8000

# Commande corrigée pour Render
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"