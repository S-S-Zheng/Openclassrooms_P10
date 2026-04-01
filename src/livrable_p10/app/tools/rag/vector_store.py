# # utils/vector_store.py
# import os
# import pickle
# import faiss
# import numpy as np
# import logging
# from typing import List, Dict, Optional

# # EN V1.x, on n'importe pas depuis .client
# from mistralai.client import MistralClient # <-- C'est "MistralClient" en v1, pas "Mistral"
# from mistralai.extra.exceptions import MistralClientException
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document # Utilisé pour le format attendu par le splitter

# from .config import (
#     MISTRAL_API_KEY, EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE,
#     FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP
# )

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class VectorStoreManager:
#     """Gère la création, le chargement et la recherche dans un index Faiss."""

#     def __init__(self):
#         self.index: Optional[faiss.Index] = None
#         self.document_chunks: List[Dict[str, any]] = [] # type:ignore
#         self.mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
#         self._load_index_and_chunks()

#     def _load_index_and_chunks(self):
#         """Charge l'index Faiss et les chunks si les fichiers existent."""
#         if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE): # type:ignore
#             try:
#                 logging.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
#                 self.index = faiss.read_index(FAISS_INDEX_FILE)
#                 logging.info(f"Chargement des chunks depuis {DOCUMENT_CHUNKS_FILE}...")
#                 with open(DOCUMENT_CHUNKS_FILE, 'rb') as f: # type:ignore
#                     self.document_chunks = pickle.load(f)
#                 logging.info(
#                     f"Index ({self.index.ntotal} vecteurs) et" # type:ignore
#                     f"{len(self.document_chunks)} chunks chargés."
#                 )
#             except Exception as e:
#                 logging.error(f"Erreur lors du chargement de l'index/chunks: {e}")
#                 self.index = None
#                 self.document_chunks = []
#         else:
#             logging.warning("Fichiers d'index Faiss ou de chunks non trouvés. L'index est vide.")

#     def _split_documents_to_chunks(
#         self,
#         documents: List[Dict[str, any]] # type:ignore
#     ) -> List[Dict[str, any]]: # type:ignore
#         """Découpe les documents en chunks avec métadonnées."""
#         logging.info(
#             f"Découpage de {len(documents)} documents en chunks"
#             f"(taille={CHUNK_SIZE}, chevauchement={CHUNK_OVERLAP})..."
#         )
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=CHUNK_SIZE,
#             chunk_overlap=CHUNK_OVERLAP,
#             length_function=len, # Important: mesure en caractères
#             add_start_index=True, # Ajoute la position de début du chunk dans le document original
#         )

#         all_chunks = []
#         doc_counter = 0
#         for doc in documents:
#             # Convertit notre format de document en format Langchain Document pour le splitter
#             langchain_doc = Document(page_content=doc["page_content"], metadata=doc["metadata"])
#             chunks = text_splitter.split_documents([langchain_doc])
#             logging.info(
#                 f"  Document '{doc['metadata'].get('filename', 'N/A')}'"
#                 f"découpé en {len(chunks)} chunks."
#             )

#             # Enrichit chaque chunk avec des métadonnées supplémentaires
#             for i, chunk in enumerate(chunks):
#                 chunk_dict = {
#                     "id": f"{doc_counter}_{i}",# Identifiant unique du chunk (doc_index_chunk_index)
#                     "text": chunk.page_content,
#                     "metadata": {
#                         **chunk.metadata,# Métadonnées héritées du document (source, category, etc.)
#                         "chunk_id_in_doc": i, # Position du chunk dans son document d'origine
#                         "start_index": chunk.metadata.get(
#                             "start_index",
#                             -1
#                         ) # Position de début (en caractères)
#                     }
#                 }
#                 all_chunks.append(chunk_dict)
#             doc_counter += 1

#         logging.info(f"Total de {len(all_chunks)} chunks créés.")
#         return all_chunks

#     def _generate_embeddings(
#         self,
#         chunks: List[Dict[str, any]] # type:ignore
#     ) -> Optional[np.ndarray]:
#         """Génère les embeddings pour une liste de chunks via l'API Mistral."""
#         if not MISTRAL_API_KEY:
#             logging.error("Impossible de générer les embeddings: MISTRAL_API_KEY manquante.")
#             return None
#         if not chunks:
#             logging.warning("Aucun chunk fourni pour générer les embeddings.")
#             return None

#         logging.info(
#             f"Génération des embeddings pour {len(chunks)} chunks (modèle: {EMBEDDING_MODEL})..."
#         )
#         all_embeddings = []
#         total_batches = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

#         for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
#             batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
#             batch_chunks = chunks[i:i + EMBEDDING_BATCH_SIZE]
#             texts_to_embed = [chunk["text"] for chunk in batch_chunks]

#             logging.info(
#                 f"  Traitement du lot {batch_num}/{total_batches} ({len(texts_to_embed)} chunks)"
#             )
#             try:
#                 response = self.mistral_client.embeddings.create(
#                     model=EMBEDDING_MODEL,
#                     inputs=texts_to_embed
#                 )
#                 batch_embeddings = [data.embedding for data in response.data]
#                 all_embeddings.extend(batch_embeddings)
#             except MistralClientException as e:
#                 logging.error(
#                     f"Erreur API Mistral lors de la génération d'embeddings (lot {batch_num}): {e}"
#                 )
#                 logging.error(
#                     f"  Détails: Status Code={e.status_code}, Message={e.message}") # type:ignore
#             except Exception as e:
#                 logging.error(
#                     f"Erreur inattendue lors de la génération d'embeddings (lot {batch_num}): {e}"
#                 )
#                 # Gérer l'erreur: ici on ajoute des vecteurs nuls pour ne pas bloquer
#                 num_failed = len(texts_to_embed)
#                 if all_embeddings: # Si on a déjà des embeddings, on prend la dimension du premier
#                     dim = len(all_embeddings[0])
#                 else: # Sinon, on ne peut pas déterminer la dimension, on saute ce lot
#                     logging.error(
#                         "Impossible de déterminer la dimension des embeddings, saut du lot."
#                     )
#                     continue
#                 logging.warning(
#                     f"Ajout de {num_failed} vecteurs nuls de dimension {dim} pour le lot échoué."
#                 )
#                 all_embeddings.extend([np.zeros(dim, dtype='float32')] * num_failed)

#             except Exception as e: # type:ignore
#                 logging.error(
#                     f"Erreur inattendue lors de la génération d'embeddings (lot {batch_num}): {e}"
#                 )
#                 # Gérer comme ci-dessus
#                 num_failed = len(texts_to_embed)
#                 if all_embeddings:
#                     dim = len(all_embeddings[0])
#                 else:
#                     logging.error(
#                         "Impossible de déterminer la dimension des embeddings, saut du lot."
#                     )
#                     continue
#                 logging.warning(
#                     f"Ajout de {num_failed} vecteurs nuls de dimension {dim} pour le lot échoué."
#                 )
#                 all_embeddings.extend([np.zeros(dim, dtype='float32')] * num_failed)


#         if not all_embeddings:
#             logging.error("Aucun embedding n'a pu être généré.")
#             return None

#         embeddings_array = np.array(all_embeddings).astype('float32')
#         logging.info(f"Embeddings générés avec succès. Shape: {embeddings_array.shape}")
#         return embeddings_array

#     def build_index(self, documents: List[Dict[str, any]]): # type:ignore
#         """Construit l'index Faiss à partir des documents."""
#         if not documents:
#             logging.warning("Aucun document fourni pour construire l'index.")
#             return

#         # 1. Découper en chunks
#         self.document_chunks = self._split_documents_to_chunks(documents)
#         if not self.document_chunks:
#             logging.error(
#                 "Le découpage n'a produit aucun chunk. Impossible de construire l'index."
#             )
#             return

#         # 2. Générer les embeddings
#         embeddings = self._generate_embeddings(self.document_chunks)
#         if embeddings is None or embeddings.shape[0] != len(self.document_chunks):
#             logging.error(
#                 "Problème de génération d'embeddings. Le nombre d'embeddings ne"
#                 "correspond pas au nombre de chunks."
#             )
#             # Nettoyer pour éviter un état incohérent
#             self.document_chunks = []
#             self.index = None
#             # Supprimer les fichiers potentiellement corrompus
#             if os.path.exists(FAISS_INDEX_FILE): os.remove(FAISS_INDEX_FILE) # type:ignore
#             if os.path.exists(DOCUMENT_CHUNKS_FILE): os.remove(DOCUMENT_CHUNKS_FILE) # type:ignore
#             return


#         # 3. Créer l'index Faiss optimisé pour la similarité cosinus
#         dimension = embeddings.shape[1]
#         logging.info(
#             "Création de l'index Faiss optimisé pour la similarité cosinus"
#             f"avec dimension {dimension}..."
#         )

#         # Normaliser les embeddings pour la similarité cosinus
#         faiss.normalize_L2(embeddings)

#         # Créer un index pour la similarité cosinus (IndexFlatIP = produit scalaire)
#         self.index = faiss.IndexFlatIP(dimension)
#         self.index.add(embeddings) # type:ignore
#         logging.info(f"Index Faiss créé avec {self.index.ntotal} vecteurs.")

#         # 4. Sauvegarder l'index et les chunks
#         self._save_index_and_chunks()

#     def _save_index_and_chunks(self):
#         """Sauvegarde l'index Faiss et la liste des chunks."""
#         if self.index is None or not self.document_chunks:
#             logging.warning("Tentative de sauvegarde d'un index ou de chunks vides.")
#             return

#         os.makedirs(os.path.dirname(FAISS_INDEX_FILE), exist_ok=True) # type:ignore
#         os.makedirs(os.path.dirname(DOCUMENT_CHUNKS_FILE), exist_ok=True) # type:ignore

#         try:
#             logging.info(f"Sauvegarde de l'index Faiss dans {FAISS_INDEX_FILE}...")
#             faiss.write_index(self.index, FAISS_INDEX_FILE)
#             logging.info(f"Sauvegarde des chunks dans {DOCUMENT_CHUNKS_FILE}...")
#             with open(DOCUMENT_CHUNKS_FILE, 'wb') as f: # type:ignore
#                 pickle.dump(self.document_chunks, f)
#             logging.info("Index et chunks sauvegardés avec succès.")
#         except Exception as e:
#             logging.error(f"Erreur lors de la sauvegarde de l'index/chunks: {e}")

#     def search(
#         self,
#         query_text: str,
#         k: int = 5,
#         min_score: float = None) -> List[Dict[str, any]]: # type:ignore
#         """
#         Recherche les k chunks les plus pertinents pour une requête.

#         Args:
#             query_text: Texte de la requête
#             k: Nombre de résultats à retourner
#             min_score: Score minimum (entre 0 et 1) pour inclure un résultat

#         Returns:
#             Liste des chunks pertinents avec leurs scores
#         """
#         if self.index is None or not self.document_chunks:
#             logging.warning("Recherche impossible: l'index Faiss n'est pas chargé ou est vide.")
#             return []
#         if not MISTRAL_API_KEY:
#             logging.error(
#                 "Recherche impossible: MISTRAL_API_KEY manquante pour générer"
#                 "l'embedding de la requête."
#             )
#             return []

#         logging.info(f"Recherche des {k} chunks les plus pertinents pour: '{query_text}'")
#         try:
#             # 1. Générer l'embedding de la requête
#             response = self.mistral_client.embeddings.create(
#                 model=EMBEDDING_MODEL,
#                 inputs=[query_text] # La requête doit être une liste
#             )
#             query_embedding = np.array([response.data[0].embedding]).astype('float32')

#             # Normaliser l'embedding de la requête pour la similarité cosinus
#             faiss.normalize_L2(query_embedding)

#             # 2. Rechercher dans l'index Faiss
#             # Pour IndexFlatIP: scores = produit scalaire (plus grand = meilleur)
#             # indices: index des chunks correspondants dans self.document_chunks
#             # Demander plus de résultats si un score minimum est spécifié
#             search_k = k * 3 if min_score is not None else k
#             scores, indices = self.index.search(query_embedding, search_k) # type:ignore

#             # 3. Formater les résultats
#             results = []
#             if indices.size > 0: # Vérifier s'il y a des résultats
#                 for i, idx in enumerate(indices[0]):
#                     if 0 <= idx < len(self.document_chunks): # Vérifier la validité de l'index
#                         chunk = self.document_chunks[idx]
#                         # Convertir le score en similarité (0-1)
#                         # Pour IndexFlatIP avec vecteurs normalisés, le score est déjà entre -1 et 1
#                         # On le convertit en pourcentage (0-100%)
#                         raw_score = float(scores[0][i])
#                         similarity = raw_score * 100

#                         # Filtrer les résultats en fonction du score minimum
#                         # Le min_score est entre 0 et 1, mais similarity est en pourcentage (0-100)
#                         min_score_percent = min_score * 100 if min_score is not None else 0
#                         if min_score is not None and similarity < min_score_percent:
#                             logging.debug(
#                                 f"Document filtré (score {similarity:.2f}% < minimum"
#                                 f"{min_score_percent:.2f}%)"
#                             )
#                             continue

#                         results.append({
#                             "score": similarity, # Score de similarité en pourcentage
#                             "raw_score": raw_score, # Score brut pour débogage
#                             "text": chunk["text"],
#                             "metadata": chunk["metadata"] # Contient source, category,
#                             # chunk_id_in_doc, start_index etc.
#                         })
#                     else:
#                         logging.warning(
#                             f"Index Faiss {idx} hors limites "
#                             f"(taille des chunks: {len(self.document_chunks)})."
#                         )

#             # Trier par score (similarité la plus élevée en premier)
#             results.sort(key=lambda x: x["score"], reverse=True)

#             # Limiter au nombre demandé (k) si nécessaire
#             if len(results) > k:
#                 results = results[:k]

#             if min_score is not None:
#                 min_score_percent = min_score * 100
#                 logging.info(
#                     f"{len(results)} chunks pertinents trouvés"
#                     f"(score minimum: {min_score_percent:.2f}%)."
#                 )
#             else:
#                 logging.info(f"{len(results)} chunks pertinents trouvés.")

#             return results

#         except MistralClientException as e:
#             logging.error(
#                 f"Erreur API Mistral lors de la génération de l'embedding de la requête: {e}"
#             )
#             logging.error(
#                 f"  Détails: Status Code={e.status_code}, Message={e.message}") # type:ignore
#             return []
#         except Exception as e:
#             logging.error(f"Erreur inattendue lors de la recherche: {e}")
#             return []

# ===================================== OPENAI ============================================
# # src/livrable_p10/app/tools/rag/utils/vector_store.py
# import os
# import pickle
# import faiss
# import numpy as np
# import logging
# from typing import List, Dict, Optional, Any

# from openai import OpenAI
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document

# from .config import (
#     OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, 
#     FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP
# )

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class VectorStoreManager:
#     """Gère la création, le chargement et la recherche dans un index Faiss avec OpenAI."""

#     def __init__(self):
#         self.index: Optional[faiss.Index] = None
#         self.document_chunks: List[Dict[str, Any]] = []
#         # Utilisation du client OpenAI synchrone
#         self.client = OpenAI(api_key=OPENAI_API_KEY)
#         self.model = OPENAI_EMBEDDING_MODEL
#         self._load_index_and_chunks()

#     def _load_index_and_chunks(self):
#         """Charge l'index Faiss et les chunks si les fichiers existent."""
#         if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
#             try:
#                 logging.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
#                 self.index = faiss.read_index(FAISS_INDEX_FILE)
#                 with open(DOCUMENT_CHUNKS_FILE, 'rb') as f:
#                     self.document_chunks = pickle.load(f)
#                 logging.info(f"Index ({self.index.ntotal} vecteurs) chargé.")
#             except Exception as e:
#                 logging.error(f"Erreur lors du chargement de l'index/chunks: {e}")
#         else:
#             logging.warning("Fichiers d'index Faiss non trouvés. L'index est vide.")

#     def _split_documents_to_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Découpe les documents en chunks avec métadonnées."""
#         logging.info(f"Découpage de {len(documents)} documents en chunks...")
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=CHUNK_SIZE,
#             chunk_overlap=CHUNK_OVERLAP,
#             add_start_index=True,
#         )

#         all_chunks = []
#         for doc_idx, doc in enumerate(documents):
#             langchain_doc = Document(page_content=doc["page_content"], metadata=doc["metadata"])
#             chunks = text_splitter.split_documents([langchain_doc])
            
#             for i, chunk in enumerate(chunks):
#                 all_chunks.append({
#                     "id": f"{doc_idx}_{i}",
#                     "text": chunk.page_content,
#                     "metadata": {
#                         **chunk.metadata,
#                         "chunk_id_in_doc": i,
#                         "start_index": chunk.metadata.get("start_index", -1)
#                     }
#                 })
#         return all_chunks

#     def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> Optional[np.ndarray]:
#         """Génère les embeddings via l'API OpenAI."""
#         if not chunks: return None

#         logging.info(f"Génération des embeddings OpenAI ({self.model})...")
#         texts = [c["text"] for c in chunks]
        
#         try:
#             # OpenAI accepte de grandes listes, mais on peut rester prudent sur la taille
#             response = self.client.embeddings.create(
#                 input=texts,
#                 model=self.model
#             )
#             embeddings = [record.embedding for record in response.data]
#             return np.array(embeddings).astype('float32')
#         except Exception as e:
#             logging.error(f"Erreur lors de la génération d'embeddings OpenAI: {e}")
#             return None

#     def build_index(self, documents: List[Dict[str, Any]]):
#         """Construit l'index Faiss à partir des documents."""
#         self.document_chunks = self._split_documents_to_chunks(documents)
#         embeddings = self._generate_embeddings(self.document_chunks)
        
#         if embeddings is None: return

#         # Normalisation pour similarité cosinus
#         faiss.normalize_L2(embeddings)
#         dimension = embeddings.shape[1]
        
#         # IndexFlatIP = Produit Scalaire (Cos-Sim si normalisé)
#         self.index = faiss.IndexFlatIP(dimension)
#         self.index.add(embeddings)
        
#         self._save_index_and_chunks()

#     def _save_index_and_chunks(self):
#         """Sauvegarde physique de l'index et des données."""
#         os.makedirs(os.path.dirname(FAISS_INDEX_FILE), exist_ok=True)
#         faiss.write_index(self.index, FAISS_INDEX_FILE)
#         with open(DOCUMENT_CHUNKS_FILE, 'wb') as f:
#             pickle.dump(self.document_chunks, f)
#         logging.info("Index et chunks sauvegardés avec succès.")

#     def search(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
#         """Recherche sémantique."""
#         if self.index is None: return []

#         # 1. Embedding de la requête
#         response = self.client.embeddings.create(input=[query_text], model=self.model)
#         query_vec = np.array([response.data[0].embedding]).astype('float32')
#         faiss.normalize_L2(query_vec)

#         # 2. Recherche
#         scores, indices = self.index.search(query_vec, k)

#         results = []
#         for i, idx in enumerate(indices[0]):
#             if 0 <= idx < len(self.document_chunks):
#                 results.append({
#                     "score": float(scores[0][i]) * 100,
#                     "text": self.document_chunks[idx]["text"],
#                     "metadata": self.document_chunks[idx]["metadata"]
#                 })
#         return results

# ===================================== HF ============================================
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
# src/livrable_p10/app/tools/rag/utils/vector_store.py
import time
import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Optional, Any, Union

# # Changement mineur d'import pour la compatibilité LangChain 0.3
# from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings
# from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


from livrable_p10.app.utils.config import (
    FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP,VECTOR_DB_DIR,
    EMBEDDING_BATCH_SIZE,
    HF_API_KEY, HF_EMBEDDING_MODEL
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
        # Initialisation de l'outil d'embedding Hugging Face
        # self.embedder = HuggingFaceInferenceAPIEmbeddings(
        #     api_key=HF_API_KEY,
        #     model_name=HF_EMBEDDING_MODEL
        # )
        # initialisation embedding local
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
                logger.info(f"Index ({self.index.ntotal} vecteurs) chargé.")
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
                    "text": chunk.page_content,
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
            # for i in range(0, len(texts), batch_size):
            #     batch_texts = texts[i:i + batch_size]

            #     # LangChain gère l'appel HTTP vers Hugging Face ici
            #     batch_encodings = self.embedder.embed_documents(batch_texts)
            #     all_embeddings.extend(batch_encodings)
            # return np.array(all_embeddings).astype('float32')
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
        self.index.add(embeddings)

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
            scores, indices = self.index.search(query_vec, k)

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