"""
Module de configuration et de gestion de la connexion PostgreSQL.

Ce module constitue le cœur de l'infrastructure de données. Il gère la construction
sécurisée de l'URL de connexion (notamment le traitement des caractères spéciaux
et l'activation du SSL pour Supabase), configure le moteur SQLAlchemy (Engine)
et fournit des générateurs de sessions pour l'API et les scripts utilitaires.
"""

# C'est le cœur de l'infrastructure de données.
# Il doit être accessible à la fois par les routes et par les scripts de création.
# Configuration de la connexion (Engine, SessionLocal)

# imports
import logging
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from livrable_p10.app.utils.config import DATABASE_URL

load_dotenv()
logger = logging.getLogger(__name__)

# =================== Mise en place ===========================

# =========================== SQLite ====================================
logging.info("Utilisation de SQLite...")
# 'check_same_thread' est spécifique à SQLite pour autoriser FastAPI
# à utiliser la même connexion sur plusieurs requêtes.
base_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal est une factory à sessions pour les routes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=base_engine)


# Fonction utilitaire pour récupérer une session de base de données
def get_db_generator():
    """
    Générateur de session de base de données.

    Crée une nouvelle session SQLAlchemy pour une opération unique et garantit
    sa fermeture systématique après utilisation, même en cas d'exception.

    Yields:
        Session: Une instance de session SQLAlchemy (SessionLocal).

    Note:
        Utilisé principalement comme dépendance injectée dans les routes FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# contextmanager est redondant pour FastAPI mais nécéssaire pour les with get_db du coup
# FASTAPI
get_db = get_db_generator

# Adaptateur pour l'utilisation via l'instruction 'with' dans les scripts Python
get_db_contextmanager = contextmanager(get_db_generator)
