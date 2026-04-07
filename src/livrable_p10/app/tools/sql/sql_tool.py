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
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine

from huggingface_hub import InferenceClient  # On passe au client officiel stable
from langchain_mistralai import ChatMistralAI


from livrable_p10.app.utils.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
    TOP_P, TEMPERATURE, MAX_TOKENS,
    MISTRAL_API_KEY, BASE_URL, MODEL_NAME,
    DATABASE_URL
)


# Configuration du logger
logger = logging.getLogger(__name__)


# ============================================================================


class SQLQueryEngine:
    """
    Moteur de conversion Langage Naturel vers SQL via LLM.
    """

    def __init__(self, database_url: str) -> None:
        """Initialise SQLAlchemy et le client Inference HF."""
        self.engine: Engine = create_engine(database_url)
        # L'InferenceClient gère lui-même les routes du routeur HF
        # self.client = InferenceClient(model=HF_MODEL_NAME, token=api_key)
        self.client = ChatMistralAI(
            model_name=MODEL_NAME,
            api_key=MISTRAL_API_KEY, #type:ignore
            temperature=0, # Le LLM doit exclusivement être factuel
            max_tokens=150, # Pas besoin d'autant qu'en sémantique
            max_retries = 1
        )
        self.prompt_sql = SQL_SYSTEM_PROMPT
        self.few_shots = SQL_FEW_SHOT

    def _clean_sql_response(self, content: str) -> str:
        """Nettoie le texte généré pour n'extraire que la requête SQL pure."""
        # Supprime le balisage Markdown si présent
        sql_query = content.replace("```sql", "").replace("```", "").strip()

        # Garde fou sur les instructions pour rester en lecture seule
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE"]
        if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
            logger.warning(f"Requête non autorisée : {sql_query}")
            raise PermissionError("Accès refusé : opération d'écriture interdite.")

        # On ne garde que la première instruction SQL pour plus de sécurité
        # if ";" in sql_query:
        #     sql_query = sql_query.split(';')[0] + ';'
        return (
            sql_query.split(';')[0] + ';' 
            if ';' in sql_query 
            else sql_query
        )

    # async def _log_report(service, query, sql, status, start_tick):
    # """S'occupe du rapprot."""
    # duration_ms = int((time.monotonic() - start_tick) * 1000)
    # try:
    #     with service.engine.begin() as conn:
    #         conn.execute(
    #             text("""
    #                 INSERT INTO reports (created_at, user_query, sql_generated, status_code,
    #                 response_time_ms)
    #                 VALUES (:now, :query, :sql, :status, :time)
    #             """),
    #             {
    #                 "now": datetime.now().isoformat(),
    #                 "query": query,
    #                 "sql": sql,
    #                 "status": status,
    #                 "time": duration_ms
    #             }
    #         )
    # except Exception as e:
    #     logger.warning(f"Logging report échoué : {e}")

    async def generate_sql(self, user_query: str) -> Optional[str]:
        """Génère une requête SQL à partir de la question utilisateur."""
        # Construction du prompt structuré
        full_prompt = (
            f"{self.prompt_sql}\n\n{self.few_shots}\n\nQuestion: {user_query}\nSQL:"
        )
        try:
            # Correction syntaxe LangChain : .ainvoke() et .content
            response = await self.client.ainvoke(full_prompt)
            content = response.content
            if not content or len(content) < 5:
                raise ValueError("Le LLM a renvoyé une réponse SQL vide ou trop courte.")
            # On force en string car LangChain peut renvoyer des listes de dict parfois
            return self._clean_sql_response(str(content))
        except Exception as e:
            logger.error(f"Erreur API : {e}")
            raise RuntimeError(f"Erreur API : {e}")

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Exécute la requête sur la base de données."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                # Mapping vers dictionnaire pour une lecture facile par l'Agent
                return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Erreur exécution SQL : {e}")
            raise RuntimeError(f"Erreur exécution SQL : {e}")

# ===================================================================

# async def nlp_to_sql_pipeline(query: str) -> str:
#     """Pipeline Tool pour l'Agent NBA avec logging automatique."""
#     logging.info("Lancement du tool SQL...")
#     start_time = time.monotonic()
#     # Instanciation dynamique du service
#     service = SQLQueryEngine(DATABASE_URL)

#     try:
#         # génère le sql à partir de la requete nlp
#         sql = await service.generate_sql(query)
#         if not sql:
#             # Cas où le LLM ne renvoie rien ou échoue
#             await _log_report(service, query, "FAILED", "SQL_GEN_FAILED", start_time)
#             return "Désolé, je n'ai pas pu traduire votre demande en requête SQL."

#         # lance la requete sql sur la db
#         data = service.execute_query(sql)
#         # Vérification d'erreur dans les données retournées
#         if data and isinstance(data[0], dict) and "error" in data[0]:
#             await _log_report(service, query, sql, "EXECUTION_ERROR", start_time)
#             # On pourrait lever une Exception 500 ici si on veut que l'Agent s'arrête
#             return f"Erreur lors de l'exécution SQL : {data[0]['error']}"

#         await _log_report(service, query, sql, "SUCCESS_200", start_time)
#         if not data:
#             return (
#                 f"La requête a fonctionné ({sql}) mais la base de"
#                 "données est muette pour cette recherche."
#             )
#         return f"Résultats SQL :\n{data}"

#     except PermissionError:
#         # Si _clean_sql_response a détecté un mot interdit (DROP, etc.)
#         await _log_report(service, query, "BLOCKED", "FORBIDDEN_403", start_time)
#         return "Sécurité : Cette requête contient des commandes non autorisées."

#     except Exception as e:
#         # Erreur système imprévue (Type 500)
#         await _log_report(service, query, "CRASH", "INTERNAL_ERROR_500", start_time)
#         logger.error(f"Crash tool SQL : {e}")
#         return "Une erreur interne est survenue lors de l'accès aux données."