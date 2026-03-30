# # src/livrable_p10/app/tools/sql/nlp_to_sql.py

# import logging
# from typing import List, Dict, Any, Optional
# from sqlalchemy import create_engine, text, Engine
# # from mistralai.client import Mistral
# from openai import AsyncOpenAI # Utilise le client openai standard, très stable

# from livrable_p10.app.tools.sql.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
# from livrable_p10.app.tools.rag.utils.config import DATABASE_URL, MISTRAL_API_KEY, MODEL_NAME

# # Configuration du logger
# logger = logging.getLogger(__name__)

# class SQLQueryEngine:
#     """
#     Moteur de conversion Langage Naturel vers SQL et exécution sur base NBA.
    
#     Attributes:
#         engine (Engine): Instance SQLAlchemy pour la connexion DB.
#         client (Mistral): Client API Mistral pour la génération SQL.
#     """

#     def __init__(self, database_url: str, api_key: str) -> None:
#         """Initialise le moteur avec les accès nécessaires."""
#         self.engine: Engine = create_engine(database_url)
#         # self.client: Mistral = Mistral(api_key=api_key)
#         # Configuration du client pour taper chez Mistral
#         self.client = AsyncOpenAI(
#             base_url="https://api.mistral.ai/v1", 
#             api_key=api_key
#         )

#     async def generate_sql(self, user_query: str) -> Optional[str]:
#         """
#         Transforme une question utilisateur en requête SQL via le LLM.
        
#         Args:
#             user_query: La question du coach (ex: "Top 5 scoreurs").
            
#         Returns:
#             Optional[str]: La requête SQL générée ou None en cas d'échec.
#         """
#         prompt = f"{SQL_SYSTEM_PROMPT}\n\n{SQL_FEW_SHOT}\n\nQuestion: {user_query}\nSQL:"
        
#         try:
#             response = await self.client.chat.completions.create(
#                 model=MODEL_NAME,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.0  # Précision maximale pour le SQL
#             )
#             # Correction de l'accès au contenu
#             if response and response.choices:
#                 content = response.choices[0].message.content
#                 if isinstance(content, str):
#                     sql_query: str = content.strip()
#                     return sql_query.replace("```sql", "").replace("```", "").strip()
#             return None
#         except Exception as e:
#             logger.error(f"Erreur génération SQL : {e}")
#             return None

#     def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
#         """
#         Exécute une requête SQL brute et retourne les résultats.
        
#         Args:
#             sql_query: Requête SQL valide.
            
#         Returns:
#             List[Dict[str, Any]]: Liste de lignes sous forme de dictionnaires.
#         """
#         try:
#             with self.engine.connect() as conn:
#                 result = conn.execute(text(sql_query))
#                 return [dict(row._mapping) for row in result.fetchall()]
#         except Exception as e:
#             logger.error(f"Erreur exécution SQL : {e}")
#             return [{"error": str(e)}]


# # ===================================================================


# async def nlp_to_sql_pipeline(query: str) -> str:
#     """
#     Pipeline SRP pour transformer une question en résultat textuel.
    
#     Args:
#         query: Question en langage naturel.
        
#     Returns:
#         str: Représentation textuelle des données pour l'agent.
#     """
#     service = SQLQueryEngine(DATABASE_URL, MISTRAL_API_KEY) # type:ignore
    
#     sql = await service.generate_sql(query)
#     if not sql:
#         return "Impossible de générer une requête SQL valide."
    
#     data = service.execute_query(sql)
#     return f"Résultats SQL pour '{sql}':\n{data}"

# ================================== OPENAI ==================================
# # src/livrable_p10/app/tools/sql/nlp_to_sql.py

# import logging
# from typing import List, Dict, Any, Optional
# from sqlalchemy import create_engine, text, Engine
# from openai import AsyncOpenAI

# from livrable_p10.app.tools.sql.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
# from livrable_p10.app.tools.rag.utils.config import (
#     DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL_NAME
# )

# # Configuration du logger
# logger = logging.getLogger(__name__)

# class SQLQueryEngine:
#     """
#     Moteur de conversion Langage Naturel vers SQL et exécution sur base NBA.
#     """

#     def __init__(self, database_url: str, api_key: str) -> None:
#         """Initialise le moteur avec SQLAlchemy et OpenAI."""
#         self.engine: Engine = create_engine(database_url)
#         # Client OpenAI standard (plus besoin de base_url Mistral)
#         self.client = AsyncOpenAI(api_key=api_key)

#     async def generate_sql(self, user_query: str) -> Optional[str]:
#         """
#         Transforme une question utilisateur en requête SQL via GPT-4o-mini.
#         """
#         # Construction du prompt avec tes constantes de prompts.py
#         prompt = f"{SQL_SYSTEM_PROMPT}\n\n{SQL_FEW_SHOT}\n\nQuestion: {user_query}\nSQL:"
        
#         try:
#             response = await self.client.chat.completions.create(
#                 model=OPENAI_MODEL_NAME,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.0  # Précision chirurgicale pour le SQL
#             )
            
#             if response.choices:
#                 content = response.choices[0].message.content
#                 if content:
#                     # Nettoyage des balises Markdown ```sql ... ```
#                     sql_query = content.strip()
#                     sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
#                     logger.info(f"SQL Généré : {sql_query}")
#                     return sql_query
#             return None
#         except Exception as e:
#             logger.error(f"Erreur génération SQL OpenAI : {e}")
#             return None

#     def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
#         """
#         Exécute la requête sur la base SQLite/Postgres et retourne des dicts.
#         """
#         try:
#             with self.engine.connect() as conn:
#                 result = conn.execute(text(sql_query))
#                 # Mapping des lignes en dictionnaires pour une lecture facile par l'Agent
#                 return [dict(row._mapping) for row in result.fetchall()]
#         except Exception as e:
#             logger.error(f"Erreur exécution SQL : {e}")
#             return [{"error": str(e)}]

# # ===================================================================

# async def nlp_to_sql_pipeline(query: str) -> str:
#     """
#     Fonction utilitaire (Tool) pour l'Agent Pydantic AI.
#     """
#     # On utilise les constantes OpenAI de ton config.py
#     service = SQLQueryEngine(DATABASE_URL, OPENAI_API_KEY)
    
#     sql = await service.generate_sql(query)
#     if not sql:
#         return "Désolé, je n'ai pas pu traduire cette question en requête de base de données."
    
#     data = service.execute_query(sql)
    
#     if not data:
#         return f"La requête SQL a été exécutée ({sql}) mais n'a retourné aucun résultat."
        
#     if "error" in data[0]:
#         return f"Une erreur est survenue lors de l'accès à la base de données : {data[0]['error']}"

#     return f"Données trouvées (via SQL {sql}) :\n{data}"

# ======================================= HF ===================================

# src/livrable_p10/app/tools/sql/sql_tool.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine
from huggingface_hub import InferenceClient  # On passe au client officiel stable

from livrable_p10.app.tools.sql.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
from livrable_p10.app.tools.rag.utils.config import (
    DATABASE_URL,
    HF_API_KEY, HF_MODEL_NAME
)

# Configuration du logger
logger = logging.getLogger(__name__)

class SQLQueryEngine:
    """
    Moteur de conversion Langage Naturel vers SQL via Hugging Face Inference API.
    """

    def __init__(self, database_url: str, api_key: str) -> None:
        """Initialise SQLAlchemy et le client Inference HF."""
        self.engine: Engine = create_engine(database_url)
        # L'InferenceClient gère lui-même les routes du routeur HF
        self.client = InferenceClient(model=HF_MODEL_NAME, token=api_key)

    def _clean_sql_response(self, content: str) -> str:
        """Nettoie le texte généré pour n'extraire que la requête SQL pure."""
        # Supprime le balisage Markdown si présent
        sql_query = content.replace("```sql", "").replace("```", "").strip()
        # On ne garde que la première instruction SQL pour plus de sécurité
        if ";" in sql_query:
            sql_query = sql_query.split(';')[0] + ';'
        return sql_query

    async def generate_sql(self, user_query: str) -> Optional[str]:
        """Génère une requête SQL à partir de la question utilisateur."""
        # Construction du prompt structuré
        full_prompt = f"{SQL_SYSTEM_PROMPT}\n\n{SQL_FEW_SHOT}\n\nQuestion: {user_query}\nSQL:"
        
        try:
            # Appel via InferenceClient (compatible avec ton environnement sans GPU)
            # On utilise chat_completion pour bénéficier du formatage de chat
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=150,
                temperature=0.01, # Indispensable pour la fidélité SQL
            )
            
            content = response.choices[0].message.content
            if content:
                sql_query = self._clean_sql_response(content)
                logger.info(f"SQL Généré : {sql_query}")
                return sql_query
            
            return None
        except Exception as e:
            logger.error(f"Erreur génération SQL via HF : {e}")
            return None

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Exécute la requête sur la base de données SQL locale."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                # Mapping vers dictionnaire pour une lecture facile par l'Agent
                return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Erreur exécution SQL : {e}")
            return [{"error": str(e)}]

# ===================================================================

async def nlp_to_sql_pipeline(query: str) -> str:
    """Pipeline Tool pour l'Agent NBA."""
    # Instanciation dynamique du service
    service = SQLQueryEngine(DATABASE_URL, HF_API_KEY)
    
    sql = await service.generate_sql(query)
    if not sql:
        return "Je n'ai pas pu traduire votre question en requête SQL."
    
    data = service.execute_query(sql)
    
    if not data:
        return f"Aucun résultat en base de données pour cette requête : {sql}"
        
    if isinstance(data[0], dict) and "error" in data[0]:
        return f"Erreur lors de l'accès aux données : {data[0]['error']}"

    return f"Résultats trouvés (Requête : {sql}) :\n{data}"