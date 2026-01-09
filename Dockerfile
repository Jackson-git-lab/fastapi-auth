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

# ~~NE PAS installer alembic et psycopg2-binary ici, car déjà dans requirements.txt~~

# Copier le code
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app

# Port exposé
EXPOSE 8000

# Commande corrigée : utilise python -m alembic et le port Render
CMD sh -c "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"