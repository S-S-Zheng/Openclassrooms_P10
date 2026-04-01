

# # imports
# import logfire

# from typing import Final
# from pydantic import BaseModel, Field, ConfigDict
# from pydantic_ai import Agent, RunContext
# from pydantic_ai.models.mistral import MistralModel
# # Au lieu de : from pydantic_ai.models.mistral import MistralModel
# # On utilise le wrapper OpenAI qui est beaucoup plus stable
# # from pydantic_ai.models.openai import OpenAIChatModel
# # from pydantic_ai.providers.openai import OpenAIProvider

# from livrable_p10.app.tools.sql.nlp_to_sql import nlp_to_sql_pipeline
# from livrable_p10.app.tools.rag.utils.vector_store import VectorStoreManager
# from livrable_p10.app.tools.rag.utils.config import MODEL_NAME, MISTRAL_API_KEY

# # Configuration Logfire
# logfire.configure()

# # --- Modèles et Dépendances ---

# class AgentDeps(BaseModel):
#     """Dépendances injectées dans l'agent."""
#     # Obligatoire pour les classes non-Pydantic comme VectorStoreManager
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     vector_store: VectorStoreManager
#     mistral_api_key: str

# class NBAQueryResponse(BaseModel):
#     """Schéma de sortie validé."""
#     answer: str = Field(description="Réponse synthétisée pour le coach")
#     source_type: str = Field(description="Source : 'SQL' ou 'RAG'")

# # --- Initialisation de l'Agent ---
# # # 1. Création du Provider avec les paramètres Mistral
# # # On passe la base_url et l'api_key directement comme admis par ta signature
# # mistral_provider = OpenAIProvider(
# #     base_url="https://api.mistral.ai/v1",
# #     api_key=MISTRAL_API_KEY
# # )
# # # 2. Instanciation du Modèle
# # # Premier argument positionnel : model_name (str)
# # # Argument nommé : provider
# # mistral_model: Final = OpenAIChatModel(
# #     MODEL_NAME, 
# #     provider=mistral_provider
# # )
# mistral_model = MistralModel(MODEL_NAME, api_key=MISTRAL_API_KEY) #type:ignore

# # Agent sans contrainte de type de sortie (renvoie un str par défaut)
# nba_agent = Agent(
#     mistral_model,
#     deps_type=AgentDeps,
#     system_prompt=(
#         "Tu es l'assistant NBA. Utilise get_player_stats pour le SQL "
#         "et get_text_archive pour le RAG. Réponds de manière concise."
#     )
# )

# # --- Outils (Typage explicite du RunContext) ---

# @nba_agent.tool
# async def get_player_stats(ctx: RunContext[AgentDeps], user_query: str) -> str:
#     """
#     Appelle cet outil pour TOUTE question numérique (points, moyennes, records).
#     Effectue une recherche dans la base de données SQL.
#     """
#     # On délègue au pipeline qui gère déjà le prompt et l'exécution
#     return await nlp_to_sql_pipeline(user_query)

# @nba_agent.tool
# def get_text_archive(ctx: RunContext[AgentDeps], user_query: str) -> str:
#     """
#     Appelle cet outil pour les questions sur l'ambiance, les rumeurs ou la philosophie de jeu.
#     """
#     # Ton VectorStoreManager.search est synchrone, on l'appelle normalement
#     results = ctx.deps.vector_store.search(user_query, k=3)
#     if not results:
#         return "Aucune archive trouvée pour cette requête."
#     return "\n\n".join([result['text'] for result in results])


# # --- Point d'entrée ---

# async def run_nba_assistant(query: str):
#     """
#     Point d'entrée de l'assistant. 
#     L'accès au résultat se fait via .data uniquement si result_type est défini.
#     """
#     vsm = VectorStoreManager()
#     deps = AgentDeps(vector_store=vsm, mistral_api_key=MISTRAL_API_KEY) #type:ignore
    
#     result = await nba_agent.run(query, deps=deps)
    
#     # Si ton IDE râle encore sur .data, c'est un bug de découverte de type.
#     # On peut forcer le cast pour rassurer le LSP, mais .data est bien l'attribut standard.
#     return result.data #type:ignore

# =============================== OPENAI ======================================

# # imports
# import logfire

# from typing import Final
# from pydantic import BaseModel, Field, ConfigDict
# from pydantic_ai import Agent, RunContext
# from pydantic_ai.models.mistral import MistralModel
# # Au lieu de : from pydantic_ai.models.mistral import MistralModel
# # On utilise le wrapper OpenAI qui est beaucoup plus stable
# from pydantic_ai.models.openai import OpenAIChatModel
# from pydantic_ai.providers.openai import OpenAIProvider

# from livrable_p10.app.tools.sql.nlp_to_sql import nlp_to_sql_pipeline
# from livrable_p10.app.tools.rag.utils.vector_store import VectorStoreManager
# from livrable_p10.app.tools.rag.utils.config import (
#     MODEL_NAME, MISTRAL_API_KEY,
#     OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, OPENAI_MODEL_NAME
# )
# # Configuration Logfire
# logfire.configure()

# # --- Modèles et Dépendances ---

# class AgentDeps(BaseModel):
#     """Dépendances injectées dans l'agent."""
#     # Obligatoire pour les classes non-Pydantic comme VectorStoreManager
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     vector_store: VectorStoreManager
#     api_key: str

# class NBAQueryResponse(BaseModel):
#     """Schéma de sortie validé."""
#     answer: str = Field(description="Réponse synthétisée pour le coach")
#     source_type: str = Field(description="Source : 'SQL' ou 'RAG'")

# # --- Initialisation de l'Agent ---
# # # 1. Création du Provider avec les paramètres Mistral
# # # On passe la base_url et l'api_key directement comme admis par ta signature
# # mistral_provider = OpenAIProvider(
# #     base_url="https://api.mistral.ai/v1",
# #     api_key=MISTRAL_API_KEY
# # )
# # # 2. Instanciation du Modèle
# # # Premier argument positionnel : model_name (str)
# # # Argument nommé : provider
# # mistral_model: Final = OpenAIChatModel(
# #     MODEL_NAME, 
# #     provider=mistral_provider
# # )
# # mistral_model = MistralModel(MODEL_NAME, api_key=MISTRAL_API_KEY) #type:ignore
# model = OpenAIChatModel(OPENAI_MODEL_NAME)

# # Agent sans contrainte de type de sortie (renvoie un str par défaut)
# nba_agent = Agent(
#     model,
#     deps_type=AgentDeps,
#     system_prompt=(
#         "Tu es l'assistant NBA. Utilise get_player_stats pour le SQL "
#         "et get_text_archive pour le RAG. Réponds de manière concise."
#     )
# )

# # --- Outils (Typage explicite du RunContext) ---

# @nba_agent.tool
# async def get_player_stats(ctx: RunContext[AgentDeps], user_query: str) -> str:
#     """
#     Appelle cet outil pour TOUTE question numérique (points, moyennes, records).
#     Effectue une recherche dans la base de données SQL.
#     """
#     # On délègue au pipeline qui gère déjà le prompt et l'exécution
#     return await nlp_to_sql_pipeline(user_query)

# @nba_agent.tool
# def get_text_archive(ctx: RunContext[AgentDeps], user_query: str) -> str:
#     """
#     Appelle cet outil pour les questions sur l'ambiance, les rumeurs ou la philosophie de jeu.
#     """
#     # Ton VectorStoreManager.search est synchrone, on l'appelle normalement
#     results = ctx.deps.vector_store.search(user_query, k=3)
#     if not results:
#         return "Aucune archive trouvée pour cette requête."
#     return "\n\n".join([result['text'] for result in results])


# # --- Point d'entrée ---

# async def run_nba_assistant(query: str):
#     """
#     Point d'entrée de l'assistant. 
#     L'accès au résultat se fait via .data uniquement si result_type est défini.
#     """
#     vsm = VectorStoreManager()
#     deps = AgentDeps(vector_store=vsm, api_key=OPENAI_API_KEY) #type:ignore
    
#     result = await nba_agent.run(query, deps=deps)
    
#     # Si ton IDE râle encore sur .data, c'est un bug de découverte de type.
#     # On peut forcer le cast pour rassurer le LSP, mais .data est bien l'attribut standard.
#     return result.data #type:ignore

# ============================== HF ==========================================

# src/livrable_p10/app/main.py
import logfire
import asyncio
import logging
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# On importe tes versions "nettoyées"
from livrable_p10.app.tools.sql.sql_tool import nlp_to_sql_pipeline
from livrable_p10.app.tools.rag.vector_store import VectorStoreManager
from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME,HF_BASE_URL
)
from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT

# Configuration Logfire
logfire.configure()
logging.basicConfig(level=logging.INFO)
# Dire à logfire de surveiller pydantic-ai
logfire.instrument_pydantic_ai()

# --- Modèles et Dépendances ---

class AgentDeps(BaseModel):
    """Dépendances injectées dans l'agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    vector_store: VectorStoreManager

# --- Configuration du Modèle via le Routeur HF ---

# Note : Pour PydanticAI, on utilise l'URL du routeur sans le nom du modèle à la fin,
# car PydanticAI l'ajoutera lui-même dans la requête POST.

# 1. Création du Provider avec les paramètres Mistral
# On passe la base_url et l'api_key directement comme admis par ta signature
hf_provider = OpenAIProvider(
    base_url=HF_BASE_URL,
    api_key=HF_API_KEY
)
# 2. Instanciation du Modèle
# Premier argument positionnel : model_name (str)
# Argument nommé : provider
hf_model = OpenAIChatModel(
    model_name=HF_MODEL_NAME, 
    provider=hf_provider
)

# --- Initialisation de l'Agent ---

nba_agent = Agent(
    hf_model,
    deps_type=AgentDeps,
    system_prompt=AGENT_SYSTEM_PROMPT
)

# --- Outils (Tools) ---

@nba_agent.tool
async def get_player_stats(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """Recherche numérique SQL (points, records, stats d'équipe)."""
    logging.info(f"Agent appelle SQL pour : {user_query}")
    return await nlp_to_sql_pipeline(user_query)

@nba_agent.tool
def get_text_archive(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """Recherche sémantique RAG (articles, ambiance, avis des fans)."""
    logging.info(f"Agent appelle RAG pour : {user_query}")
    results = ctx.deps.vector_store.search(user_query, k=3)

    if not results:
        return "Aucune archive textuelle trouvée pour cette question."

    formatted_results = [
        f"Score:[{result['score']}%] - Contenu: {result['text']} "
        f"(Source: {result['metadata'].get('source', 'Inconnue')})"
        for result in results
    ]
    return "\n\n".join(formatted_results)

# --- Point d'entrée ---

async def run_nba_assistant(query: str):
    """Initialise les composants et lance l'agent."""
    # Le VectorStoreManager charge l'index existant
    vsm = VectorStoreManager()
    deps = AgentDeps(vector_store=vsm)

    try:
        # L'exécution de l'agent
        result = await nba_agent.run(query, deps=deps)
        # 1. Tentative Pydantic AI standard (version récente)
        if hasattr(result, 'data'):
            return result.data
        # 2. Tentative via l'attribut 'new_data' (certaines versions beta)
        if hasattr(result, 'new_data'):
            return result.new_data
        # 3. Récupération du dernier message de l'assistant (méthode universelle)
        if hasattr(result, 'all_messages'):
            last_msg = result.all_messages()[-1]
            # Si c'est un ModelResponse
            if hasattr(last_msg, 'parts'):
                return last_msg.parts[0].content
        # 4. Ultime secours : on renvoie l'objet tel quel
        return str(result)

    except Exception as e:
        logging.error(f"Erreur Agent : {e}")
        return f"Une erreur est survenue : {str(e)}"

if __name__ == "__main__":
    # Test rapide
    question = "Compare les stats de Curry avec ce que les gens pensent de sa forme."
    answer = asyncio.run(run_nba_assistant(question))
    print(f"\nRÉPONSE DE L'AGENT :\n{answer}")