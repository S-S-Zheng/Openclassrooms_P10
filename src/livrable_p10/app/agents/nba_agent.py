"""
Module d'orchestration de l'Agent intelligent NBA.

Ce module définit l'Agent Pydantic AI, ses dépendances (VectorStore, SQL) 
et ses outils. Il utilise un LLM pour raisonner et choisir entre une recherche
sémantique ou une requête SQL.
"""

# Imports
import logfire
import logging

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from livrable_p10.app.tools.sql.sql_pipeline import nlp_to_sql_pipeline
from livrable_p10.app.tools.semantic.vector_store import VectorStoreManager
from livrable_p10.app.utils.config import (
    SEARCH_K, TOP_P, TEMPERATURE, MAX_TOKENS, MISTRAL_API_KEY, MODEL_NAME
)
from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT_AFTER, AGENT_FEW_SHOTS


logger = logging.getLogger(__name__)


# ==============================================================================
# --- Modèles et Dépendances ---

class AgentDeps(BaseModel):
    """
    Dépendances injectées dans l'Agent au moment de l'exécution.

    Attributes:
        vector_store: Gestionnaire de la base de données vectorielle.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)# Pydantic ne stop pas VectorStoreManager
    vector_store: VectorStoreManager

# --- Configuration du modèle de langage (LLM) ---
# Pour PydanticAI, on utilise l'URL du routeur sans le nom du modèle à la fin,
# car PydanticAI l'ajoutera lui-même dans la requête POST.

# 1. Création du Provider
# Le Provider gère l'authentification
mistral_provider = MistralProvider(
    # base_url=BASE_URL,
    api_key=MISTRAL_API_KEY
)
# 2. Instanciation du Modèle
# Premier argument positionnel : model_name (str)
# Argument nommé : provider
mistral_model = MistralModel(
    model_name=MODEL_NAME,
    provider= mistral_provider,
    settings={
        "temperature":TEMPERATURE,
        "max_tokens":MAX_TOKENS,
        "top_p":TOP_P,
        "max_retries":1
    } #type:ignore
)

# =================================================================
# --- Initialisation de l'Agent ---
nba_agent = Agent(
    mistral_model,
    deps_type=AgentDeps,
    # system_prompt=AGENT_SYSTEM_PROMPT_AFTER,
)
@nba_agent.system_prompt
def add_rules(ctx: RunContext[AgentDeps]) -> str:
    return AGENT_SYSTEM_PROMPT_AFTER

@nba_agent.system_prompt
def add_examples(ctx: RunContext[AgentDeps]) -> str:
    return AGENT_FEW_SHOTS

# =================================================================
# --- Outils (Tools) ---

@nba_agent.tool
# ctx est une obligation de signature. Même si tu ne l'utilises pas, Pydantic AI injecte toujours
# le contexte d'exécution (RunContext) comme premier argument de tes outils.
async def ask_database(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """
    Accès aux statistiques NBA structurées (Points, moyennes, records).
    Utilisé pour les questions factuelles et chiffrées.
    """
    logging.info(f"Agent appelle SQL pour : {user_query}")
    return await nlp_to_sql_pipeline(user_query)

@nba_agent.tool
def ask_index(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """
    Accès au contexte sémantique (Articles, opinions des fans, histoire).
    Utilisé pour les questions subjectives ou contextuelles.
    """
    logging.info(f"Agent appelle index pour : {user_query}")
    results = ctx.deps.vector_store.search(user_query, k=SEARCH_K)
    if not results:
        return "Aucune archive textuelle trouvée pour cette question."
    # Formatage des documents pour le contexte du LLM
    formatted_results = [
        f"(Sujet: {result['metadata'].get('title', 'Sans titre')}) | {result['text']}"
        for result in results
    ]
    return "\n\n".join(formatted_results)


# ======================= MOTEUR D'EXÉCUTION (WRAPPER) ==============================

class NBAEngine:
    """
    Moteur principal orchestrant l'Agent et ses ressources.\n
    Centralise le VectorStore et fournit une interface simple
    pour les requêtes utilisateurs et l'évaluation.
    """
    def __init__(self):
        self.vsm = VectorStoreManager()
        self.deps = AgentDeps(vector_store=self.vsm)

    async def run_nba_assistant(self, question: str) -> str:
        """
        Exécute l'agent sur une question donnée avec un tracing Logfire.

        Args:
            question (str): La question posée par l'utilisateur.

        Returns:
            str: La réponse textuelle générée par l'agent.
        """
        # Cette ligne lie la question à tous les logs qui suivent (SQL, Index, LLM)
        with logfire.span("Requête Agent: {question}", question=question):
            try:
                # L'exécution de l'agent
                result = await nba_agent.run(question, deps=self.deps)
                # # 1. Tentative Pydantic AI standard (version récente)
                # if hasattr(result, 'data'):
                #     return result.data
                # # 2. Tentative via l'attribut 'new_data' (certaines versions beta)
                # if hasattr(result, 'new_data'):
                #     return result.new_data
                # # 3. Récupération du dernier message de l'assistant (méthode universelle)
                if hasattr(result, 'all_messages'):
                    last_msg = result.all_messages()[-1]
                    # Si c'est un ModelResponse
                    if hasattr(last_msg, 'parts'):
                        return last_msg.parts[0].content #type:ignore
                # 4. Ultime secours : on renvoie l'objet tel quel
                return str(result)

            except Exception as e:
                logging.error(f"Erreur Agent : {e}")
                return f"Une erreur est survenue : {str(e)}"

    async def get_eval_data(self, question: str) -> dict:
        """
        Méthode spécifique pour l'évaluation Ragas.

        Args:
            question (str): La question de test.

        Returns:
            dict: Contient la réponse ('answer') et les contextes extraits ('contexts').
        """
        # Extraction manuelle des contextes pour eval
        contexts = [result['text'] for result in self.vsm.search(question, k=SEARCH_K)]
        answer = await self.run_nba_assistant(question)
        return {
            "answer": answer,
            "contexts": contexts
        }