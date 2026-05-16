# --- Étape 1 : Build (Installation des dépendances) ---
FROM python:3.12-slim AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true\
    POETRY_VIRTUALENVS_CREATE=true

# Installation des dépendances système nécessaires à la compilation (gcc, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && rm -rf /var/lib/apt/lists/*

# Installation de Poetry 2.0
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copie des fichiers de config uniquement (pour le cache Docker)
COPY pyproject.toml poetry.lock ./ 
# Installation dépendances
RUN poetry install --only main --no-root

# --- Étape 2 : Runtime (Image finale légère) ---
FROM python:3.12-slim AS runtime

# On définit le dossier de travail à la racine de l'application
WORKDIR /app
# Installation des dépendances système pour l'exécution (copie du builder)
COPY --from=builder /app/.venv /app/.venv

# On propage le PYTHONPATH pour que livrable_p12 soit reconnu
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

# Copie des élements
COPY src/ ./src/
COPY datas/NBA_database/interactions.db ./datas/NBA_database/
COPY datas/vector_db/document_chunks.pkl ./datas/vector_db/
COPY datas/vector_db/faiss_index.idx ./datas/vector_db/

# Droits pour Hugging Face (User 1000)
RUN useradd -m -u 1000 nbauser && chown -R nbauser:nbauser /app
# utilisateur non-root pour la sécurité
USER nbauser

# Port par défaut pour HF
EXPOSE 7860

# Lancement de Streamlit directement
CMD ["streamlit", "run", "main.py", "--server.port", "7860", "--server.address", "0.0.0.0"]