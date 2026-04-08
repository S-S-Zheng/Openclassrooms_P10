"""
Moteur de génération et d'exécution SQL

Ce module transforme les prompts enrichis en requêtes SQL valides.
Gère la sécurité (lecture seule) et valide les données de sortie.
"""
# Imports
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, text, Engine
from langchain_mistralai import ChatMistralAI


from livrable_p10.app.utils.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
from livrable_p10.app.utils.config import (
    MISTRAL_API_KEY, MODEL_NAME
)
from livrable_p10.app.utils.schemas import SQLOutputSchema

# Configuration du logger
logger = logging.getLogger(__name__)


# ============================================================================


class SQLQueryEngine:
    """
    Moteur gérant l'interface entre le LLM et la base de données SQL.

    Responsabilités
    -----
    1. Instancier le client LLM pour la génération SQL.
    2. Nettoyer et sécuriser les requêtes (prévention d'injections).
    3. Exécuter les requêtes et valider les résultats via Pydantic.
    """

    def __init__(self, database_url: str) -> None:
        """
        Initialise la connexion entre la base et le LLM.

        Args:
            database_url (str): URL de connexion à la base.
        """
        self.engine: Engine = create_engine(database_url)
        # L'InferenceClient gère lui-même les routes du routeur HF
        # self.client = InferenceClient(model=HF_MODEL_NAME, token=api_key)
        self.client = ChatMistralAI(
            model_name=MODEL_NAME,
            api_key=MISTRAL_API_KEY, #type:ignore
            temperature=0.0, # Le LLM doit exclusivement être factuel
            max_tokens=250, # Pas besoin d'autant qu'en sémantique
            max_retries = 3,
            timeout = 60
        )
        self.prompt_sql = SQL_SYSTEM_PROMPT
        self.few_shots = SQL_FEW_SHOT

    def _clean_sql_response(self, content: str) -> str:
        """
        Nettoie et sécurise la chaîne renvoyée par le LLM.

        Args:
            content (str): Réponse brute du LLM.

        Returns:
            str: Requête SQL propre ou code d'erreur métier.

        Raises:
            PermissionError: Si un mot-clé SQL interdit est détecté.
        """
        # on a dit dans le prompt de générer ça si, hallucination sql avec plus de 3 imbrications)
        if "DATA_NOT_AVAILABLE" in content:
            return "DATA_NOT_AVAILABLE"

        # Supprime le balisage Markdown si présent
        sql_query = content.replace("```sql", "").replace("```", "").strip()

        # Garde fou sur les instructions pour rester en lecture seule pour le LLM
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT"]
        if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
            logger.warning(f"Requête non autorisée : {sql_query}")
            raise PermissionError("Accès refusé : opération d'écriture interdite.")

        # On ne garde que la première instruction SQL pour plus de sécurité
        return (
            sql_query.split(';')[0] + ';' 
            if ';' in sql_query 
            else sql_query
        )

    async def generate_sql(self, user_query: str) -> Optional[str]:
        """
        Construit le prompt complet et appelle le LLM pour générer le SQL.

        Args:
            user_query (str): La question de l'utilisateur.

        Returns:
            str: La requête SQL nettoyée.
        """
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
        """
        Exécute la requête SQL et valide chaque ligne avec le schéma Pydantic.

        Args:
            sql_query (str): Requête SQL à exécuter.

        Returns:
            List[Dict[str, Any]]: Liste de résultats nettoyés (sans valeurs None).
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                # Mapping vers dictionnaire pour une lecture facile par l'Agent
                raw_rows = [dict(row._mapping) for row in result.fetchall()]
                # Validation Pydantic
                validated_rows = []
                for row in raw_rows:
                    # model_validate avec extra='allow' garde les colonnes calculées par le LLM
                    # tout en typant correctement name, points, ppg, etc.
                    obj = SQLOutputSchema.model_validate(row)
                    # On ne garde que ce qui n'est pas None pour économiser les tokens
                    validated_rows.append(obj.model_dump(exclude_none=True))
                return validated_rows
        except Exception as e:
            logger.error(f"Erreur exécution SQL : {e}")
            raise RuntimeError(f"Erreur exécution SQL : {e}")