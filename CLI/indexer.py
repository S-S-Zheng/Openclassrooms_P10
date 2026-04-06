# # indexer.py
# import argparse
# import logging
# from typing import Optional

# from utils.config import INPUT_DIR # INPUT_DATA_URL (décommentez si besoin)
# from utils.data_loader import download_and_extract_zip, load_and_parse_files
# from utils.vector_store import VectorStoreManager

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def run_indexing(input_directory: str, data_url: Optional[str] = None):
#     """Exécute le processus complet d'indexation."""
#     logging.info("--- Démarrage du processus d'indexation ---")

#     # --- Étape 1: Téléchargement et Extraction (Optionnel) ---
#     if data_url:
#         logging.info(f"Tentative de téléchargement depuis l'URL: {data_url}")
#         success = download_and_extract_zip(data_url, input_directory)
#         if not success:
#             logging.error("Échec du téléchargement ou de l'extraction. Arrêt.")
#             # Décider si on continue avec le contenu local existant ou si on arrête.
#             # Ici, on arrête pour éviter d'indexer des données potentiellement incomplètes/anciennes.
#             return
#     else:
#         logging.info(f"Aucune URL fournie. Utilisation des fichiers locaux dans: {input_directory}")

#     # --- Étape 2: Chargement et Parsing des Fichiers ---
#     logging.info(f"Chargement et parsing des fichiers depuis: {input_directory}")
#     documents = load_and_parse_files(input_directory)

#     if not documents:
#         logging.warning("Aucun document n'a été chargé ou parsé. Vérifiez le contenu du dossier d'entrée.")
#         logging.info("--- Processus d'indexation terminé (aucun document traité) ---")
#         return

#     # --- Étape 3: Création/Mise à jour de l'index Vectoriel ---
#     logging.info("Initialisation du gestionnaire de Vector Store...")
#     vector_store = VectorStoreManager() # Le constructeur ne fait que charger s'il existe

#     logging.info("Construction de l'index Faiss (cela peut prendre du temps)...")
#     # Cette méthode va splitter, générer les embeddings, créer l'index et sauvegarder
#     vector_store.build_index(documents)

#     logging.info("--- Processus d'indexation terminé avec succès ---")
#     logging.info(f"Nombre de documents traités: {len(documents)}")
#     if vector_store.index:
#         logging.info(f"Nombre de chunks indexés: {vector_store.index.ntotal}")
#     else:
#         logging.warning("L'index final n'a pas pu être créé ou est vide.")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Script d'indexation pour l'application RAG")
#     parser.add_argument(
#         "--input-dir",
#         type=str,
#         default=INPUT_DIR,
#         help=f"Répertoire contenant les fichiers sources (par défaut: {INPUT_DIR})"
#     )
#     parser.add_argument(
#         "--data-url",
#         type=str,
#         # default=INPUT_DATA_URL, # Décommentez pour utiliser la valeur du .env par défaut
#         default=None,
#         help="URL optionnelle pour télécharger et extraire un fichier inputs.zip"
#     )
#     args = parser.parse_args()

#     # Vérifier si l'URL est passée en argument, sinon prendre celle du .env (si définie)
#     # final_data_url = args.data_url if args.data_url is not None else INPUT_DATA_URL
#     # Simplification: on utilise seulement l'argument --data-url pour l'instant
#     final_data_url = args.data_url

#     run_indexing(input_directory=args.input_dir, data_url=final_data_url)

# ==============================================================================
"""
Pipeline d'indexation -> extraction, nettoyage et chargement des documents dans Faiss.

Workflow
--------
Récupère les arguments (dossier, URL) via ``argparse``
* EXTRAIT la donnée (traite un ZIP si une URL est fournie) via ``data_loader.py``.
* Lit ensuite les PDF/Excel et les TRANSFORME en objets "documents" bruts via ``data_loader.py``
* LOAD la donnée en déclenchant le chunking et la création de l'index Faiss via ``vector_store.py``.

IMPORTANT
--------
Fait partie du groupe de fichiers fourni, mais correctifs important nécéssaire
car non fonctionnel.
"""

# indexer.py
import argparse
import logging
from typing import Optional, List, Any
import os
import pickle


from livrable_p10.app.utils.config import (
    INPUT_DIR, VECTOR_DB_DIR, BLACKLIST_FILE)
from livrable_p10.app.utils.data_loader import (
    download_and_extract_zip,
    load_and_parse_files
)
from livrable_p10.app.tools.semantic.vector_store import VectorStoreManager
from livrable_p10.app.utils.document_reshape import get_clean_and_entitle

# Configuration du logger centralisée
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =========================================================================


def run_indexing(input_directory: str, data_url: Optional[str] = None) -> None:
    """
    Orchestre le processus complet d'indexation des documents.

    Args:
        input_directory (str): Chemin vers le dossier contenant les documents à indexer.
        data_url (Optional[str]): URL vers un fichier .zip contenant les données (optionnel).

    Returns:
        None
    """
    logging.info("--- Démarrage du processus d'indexation ---")

    # --- Étape 1: Téléchargement et Extraction (Optionnel) ---
    if data_url:
        logging.info(f"Tentative de téléchargement depuis l'URL: {data_url}")
        success = download_and_extract_zip(data_url, input_directory)
        if not success:
            logging.error("Échec du téléchargement ou de l'extraction. Arrêt.")
            # Décider si on continue avec le contenu local existant ou si on arrête.
            # Ici, on arrête pour éviter d'indexer des données potentiellement incomplètes/anciennes
            return
    else:
        logging.info(f"Aucune URL fournie. Utilisation des fichiers locaux dans: {input_directory}")

    # --- Étape 2: Chargement et Parsing des Fichiers ---
    # logging.info(f"Chargement et parsing des fichiers depuis: {input_directory}")
    # On précise que documents est une liste (le type exact dépend du loader, souvent List[Dict])
    # documents: List[Any] = load_and_parse_files(input_directory)
    # On charge le fichier OCR temporaire s'il existe
    tmp_file = os.path.join(VECTOR_DB_DIR, 'tmp_ocr.pkl')
    if os.path.exists(tmp_file):
        logging.info(f"--- Chargement de l'OCR depuis le cache : {tmp_file} ---")
        with open(tmp_file, 'rb') as f:
            documents: List[Any] = pickle.load(f)
    else:
        logging.info(f"Chargement et parsing des fichiers depuis: {input_directory}")
        documents: List[Any] = load_and_parse_files(input_directory)
        # Sauvegarde immédiate après l'OCR
        with open(tmp_file, 'wb') as f:
            pickle.dump(documents, f)
        logging.info(f"--- {tmp_file} sauvegardé ---")

    if not documents:
        logging.warning(
            "Aucun document n'a été chargé ou parsé. Vérifiez le contenu du dossier d'entrée."
        )
        logging.info("--- Processus d'indexation terminé (aucun document traité) ---")
        return

    # # Persistence temporaire:
    # tmp_file = os.path.join(VECTOR_DB_DIR, 'tmp_ocr.pkl')
    # if not os.path.exists(tmp_file):
    #     with open(tmp_file, 'wb') as f:
    #         pickle.dump(documents, f)
    #     logging.info(f"--- {tmp_file} sauvegardé ---")
    # else:
    #     logging.info(f"--- {tmp_file} existe déjà, passage à l'étape suivante ---")

    # Nettoyage du bruit
    logging.info("Nettoyage du bruit post OCR...")
    cleaned_documents = get_clean_and_entitle(documents, BLACKLIST_FILE)

    # --- Étape 3: Création/Mise à jour de l'index Vectoriel ---
    logging.info("Initialisation du gestionnaire de Vector Store...")
    vector_store = VectorStoreManager() # Le constructeur ne fait que charger s'il existe

    logging.info("Construction de l'index Faiss (cela peut prendre du temps)...")
    # Cette méthode va splitter, générer les embeddings, créer l'index et sauvegarder
    vector_store.build_index(cleaned_documents)

    # --- Finalité du processus ----
    logging.info("--- Processus d'indexation terminé avec succès ---")
    logging.info(f"Nombre de documents traités: {len(cleaned_documents)}")
    if vector_store.index:
        logging.info(f"Nombre de chunks indexés: {vector_store.index.ntotal}")
    else:
        logging.warning("L'index final n'a pas pu être créé ou est vide.")


# =============================================================================


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script d'indexation pour l'application RAG")
    parser.add_argument(
        "--input-dir",
        type=str,
        default=INPUT_DIR,
        help=f"Répertoire contenant les fichiers sources (par défaut: {INPUT_DIR})"
    )
    parser.add_argument(
        "--data-url",
        type=str,
        # default=INPUT_DATA_URL, # Décommentez pour utiliser la valeur du .env par défaut
        default=None,
        help="URL optionnelle pour télécharger et extraire un fichier inputs.zip"
    )
    args = parser.parse_args()

    # Vérifier si l'URL est passée en argument, sinon prendre celle du .env (si définie)
    # final_data_url = args.data_url if args.data_url is not None else INPUT_DATA_URL
    # Simplification: on utilise seulement l'argument --data-url pour l'instant
    final_data_url = args.data_url

    run_indexing(input_directory=args.input_dir, data_url=final_data_url)