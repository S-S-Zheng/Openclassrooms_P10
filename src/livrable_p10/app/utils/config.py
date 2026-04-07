# utils/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# --- ROOT -----
ROOT_DIR = Path(__file__).parents[4]

# --- URL ---
BASE_URL = "https://api.mistral.ai/v1"
HF_BASE_URL = "https://router.huggingface.co/v1"

# --- Clé API ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")#os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print(
        "⚠️ Attention: La clé API Mistral (MISTRAL_API_KEY) n'est pas définie dans le fichier .env"
    )
    # Vous pouvez choisir de lever une exception ici ou de continuer
    # avec des fonctionnalités limitées
    # raise ValueError("Clé API Mistral manquante. Veuillez la définir dans le fichier .env")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")#os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     print(
#         "⚠️ Attention: La clé API OpenAi (OPENAI_API_KEY) n'est pas définie dans le fichier .env"
#     )
HF_API_KEY = os.getenv("HF_API_KEY")#os.getenv("HF_API_KEY")
if not HF_API_KEY:
    print(
        "⚠️ Attention: La clé API HF (HF_API_KEY) n'est pas définie dans le fichier .env"
    )

# --- Modèles ---
EMBEDDING_MODEL = "mistral-embed"
MODEL_NAME = "mistral-small-latest" # Ou un autre modèle comme mistral-large-latest
# OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
# OPENAI_MODEL_NAME = "gpt-4o-mini"
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta:featherless-ai"
# le suffixe featherless-ai: Hugging Face utilise des partenaires
# (comme Featherless ou d'autres infrastructures dédiées) pour servir
# certains modèles gratuitement de manière plus stable. Sans ce suffixe,
# le routeur cherchait l'instance "standard" qui était probablement éteinte
# ou déplacée, d'où le 404.

# --- Configuration de l'Indexation ---
# INPUT_DATA_URL = os.getenv("INPUT_DATA_URL") # Décommentez si vous utilisez une URL
# INPUT_DIR = "inputs"                # Dossier pour les données sources après extraction
# VECTOR_DB_DIR = "vector_db"         # Dossier pour stocker l'index Faiss et les chunks
# FAISS_INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss_index.idx")
# DOCUMENT_CHUNKS_FILE = os.path.join(VECTOR_DB_DIR, "document_chunks.pkl")
INPUT_DIR = str(ROOT_DIR / "datas" / "inputs")
VECTOR_DB_DIR = str(ROOT_DIR / "datas" / "vector_db")
FAISS_INDEX_FILE = str(ROOT_DIR / "datas" / "vector_db" / "faiss_index.idx")
DOCUMENT_CHUNKS_FILE = str(ROOT_DIR / "datas" / "vector_db" / "document_chunks.pkl")
BLACKLIST_FILE = str(ROOT_DIR / "src" / "livrable_p10" / "app" / "utils" / "blacklist.txt")

CHUNK_SIZE = 1000                  # Taille des chunks en *caractères* (vise ~512 tokens)
CHUNK_OVERLAP = 150                 # Chevauchement en *caractères*
EMBEDDING_BATCH_SIZE = 32           # Taille des lots pour l'API d'embedding

# --- Configuration de la Recherche ---
SEARCH_K = 3                        # Nombre de documents à récupérer par défaut

# --- Configuration de la réponse ---
MAX_TOKENS = 500
TEMPERATURE = 0.1
TOP_P = 0.9

# --- Configuration de la Base de Données ---
SQLITE_FLAG=os.getenv("SQLITE_FLAG","True")
EXCEL_INPUT=INPUT_DIR+"/regular NBA.xlsx"
DATABASE_DIR = ROOT_DIR / "datas" / "NBA_database"
DATABASE_FILE = DATABASE_DIR / "interactions.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}" # URL pour SQLAlchemy

# --- Configuration de l'Application ---
APP_TITLE = "NBA Analyst AI"
NAME = "NBA" # Nom à personnaliser dans l'interface

# --- Chemins de test et évaluation ---
QA_PATH = str(ROOT_DIR / "datas" / "qa_pairs")
RAGAS_OUTPUT = str(ROOT_DIR / "datas" / "qa_pairs" / "ragas.json")
LOGS_PATH = ROOT_DIR / "datas" / "logs"