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

# Installer Alembic pour les migrations
RUN pip install alembic psycopg2-binary

# Copier le code
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app

# Port exposé
EXPOSE 8000

# Commande par défaut
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]