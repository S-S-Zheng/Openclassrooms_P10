"""
Module de gestion de l'index. La classe ``VectorStoreManager`` s'occupe de charger si possible
un index. Elle va découper, vectoriser et persister les sources textuelles via sa méthode
``build_index`` et réalise la recherche sémantique d'une question via ``search``.

Workflow
--------
* L'instanciation va initialiser l'embeddeur à partir de la clef API et du modèle configuré.
    De plus, le constructeur va tenter de charger, s'il trouve, l'index.
* L'appel de ``build_index`` va lancer en interne, le découpage et la vectorisation des textes
    puis de sa persistence sur le disque.
* L'appel de ``search`` va transformer la question en vecteur puis faire une recherche de proximité
    avec ses k voisins les plus proches dans l'index et le RETRIEVE.

IMPORTANT
--------
Fait partie du groupe de fichiers fourni, mais correctifs important nécéssaire
car non fonctionnel.
"""
# Imports
import time
import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Optional, Any

# On utilise HuggingFace en local (telechargement des poids du modele)
# Rend gratuit, privé et illimité toute la structure d'indexation.
# Remarque: l'embedding est très leger VS le LLM --> pas de huggingfaceChat
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


from livrable_p10.app.utils.config import (
    FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP,VECTOR_DB_DIR,
    EMBEDDING_BATCH_SIZE,
    HF_EMBEDDING_MODEL
)

logger = logging.getLogger(__name__)


# ============================================================================


class VectorStoreManager:
    """
    Gère le stockage et la recherche sémantique via Faiss et Hugging Face.
    
    Cette classe permet de transformer des documents textes en vecteurs numériques
    et d'effectuer des recherches de similarité.
    """

    def __init__(self) -> None:
        """Initialise l'embedder et tente de charger l'index existant."""
        self.index: Optional[faiss.Index] = None
        self.document_chunks: List[Dict[str, Any]] = []
        # Initialisation de l'embedding local (CPU)
        # Le modèle est téléchargé au premier lancement puis réutilisé localement.
        self.embedder = HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
        )
        self._load_index_and_chunks()

    def _load_index_and_chunks(self) -> None:
        """Charge l'index Faiss et les métadonnées depuis le stockage local."""
        if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
            try:
                logger.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
                self.index = faiss.read_index(FAISS_INDEX_FILE)
                with open(DOCUMENT_CHUNKS_FILE, 'rb') as f:
                    self.document_chunks = pickle.load(f)
                logger.info(f"Index ({self.index.ntotal} vecteurs) chargé.") #type:ignore
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'index : {e}")
        else:
            logger.warning("Fichiers d'index Faiss non trouvés. L'index est vide.")

    def _split_documents_to_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Découpe les documents volumineux en fragments (chunks) plus petits.

        Args:
            documents: Liste de dictionnaires contenant 'page_content' et 'metadata'.

        Returns:
            Liste de chunks avec leurs métadonnées respectives.
        """
        logger.info(f"Découpage de {len(documents)} documents en chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            add_start_index=True,
        )

        all_chunks: List[Dict[str, Any]] = []
        for doc_idx, doc in enumerate(documents):
            langchain_doc = Document(page_content=doc["page_content"], metadata=doc["metadata"])
            chunks = text_splitter.split_documents([langchain_doc])

            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"{doc_idx}_{i}",
                    "text": (
                        f"Sujet: {chunk.metadata.get("title")}\n\n" + chunk.page_content
                    ),
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id_in_doc": i,
                        "start_index": chunk.metadata.get("start_index", -1)
                    }
                })
        return all_chunks

    def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Génère les embeddings via Hugging Face Inference API."""
        if not chunks:
            return None

        texts = [c["text"] for c in chunks]
        all_embeddings = []
        batch_size = EMBEDDING_BATCH_SIZE # Sécurité pour l'API gratuite

        logger.info(
            f"Génération des embeddings ({len(texts)} chunks) par batchs de {batch_size}..."
        )

        try:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                # TENTATIVE AVEC RETRY
                for attempt in range(3): # 3 essais par lot
                    try:
                        batch_encodings = self.embedder.embed_documents(batch_texts)
                        all_embeddings.extend(batch_encodings)
                        break # Succès, on sort de la boucle d'essai
                    except Exception as e:
                        if attempt < 2:
                            logger.warning(f"Batch échoué, nouvel essai dans 20s... ({e})")
                            time.sleep(20) # On laisse l'API respirer
                        else:
                            logger.error(f"Batch définitivement échoué après 3 tentatives.")
                            return None
                time.sleep(5) # Petite pause entre chaque batch réussi pour éviter le spam
            return np.array(all_embeddings).astype('float32')
        except Exception as e:
            logger.error(f"Erreur API Hugging Face (Embeddings) : {e}")
            return None

    def build_index(self, documents: List[Dict[str, Any]]):
        """Construit et normalise l'index pour une recherche précise."""
        self.document_chunks = self._split_documents_to_chunks(documents)
        embeddings = self._generate_embeddings(self.document_chunks)

        if embeddings is None or len(embeddings) == 0:
            logger.error("Construction annulée : aucun embedding généré.")
            return

        # Normalisation L2 = Important pour que le produit scalaire (Inner Product) 
        # se comporte comme une similarité cosinus.
        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]

        # Utilisation de IndexFlatIP (Inner Product) après normalisation
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings) #type:ignore

        self._save_index_and_chunks()

    def _save_index_and_chunks(self):
        """Sauvegarde physique de l'index et des données."""
        os.makedirs(os.path.dirname(VECTOR_DB_DIR), exist_ok=True)
        faiss.write_index(self.index, FAISS_INDEX_FILE)
        with open(DOCUMENT_CHUNKS_FILE, 'wb') as f:
            pickle.dump(self.document_chunks, f)
        logger.info("Index et chunks sauvegardés avec succès.")

    def search(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche les k passages les plus pertinents pour une requête donnée.

        Args:
            query_text: La question de l'utilisateur.
            k: Nombre de résultats à retourner.

        Returns:
            Liste de dictionnaires contenant le score, le texte et les métadonnées.
        """
        if self.index is None or not self.document_chunks:
            logger.warning("Recherche impossible : Index vide.")
            return []

        try:
            # 1. Embedding de la question
            query_embedding = self.embedder.embed_query(query_text)
            query_vec = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_vec)

            # 2. Recherche des k plus proches voisins
            scores, indices = self.index.search(query_vec, k) #type:ignore

            results: List[Dict[str, Any]] = []
            for i, idx in enumerate(indices[0]):
                # On vérifie que l'index retourné par Faiss existe dans nos chunks
                if 0 <= idx < len(self.document_chunks):
                    results.append({
                        "score": round(float(scores[0][i]) * 100, 2),
                        "text": self.document_chunks[idx]["text"],
                        "metadata": self.document_chunks[idx]["metadata"]
                    })
            return results
        except Exception as e:
            logger.error(f"Erreur lors de la recherche : {e}")
            return []