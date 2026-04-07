

# # livrable_p10/app/tools/rag/NBAAgent.py
# import logging
# from huggingface_hub import AsyncInferenceClient
# from openai import AsyncOpenAI
# from langchain_mistralai import ChatMistralAI

# from livrable_p10.app.utils.config import (
#     HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
#     TOP_P, TEMPERATURE, MAX_TOKENS,
#     MISTRAL_API_KEY, BASE_URL, MODEL_NAME
# )
# from livrable_p10.app.tools.semantic.vector_store import VectorStoreManager
# from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT_BEFORE

# logger = logging.getLogger(__name__)


# # ============================================================


# class NBAAgent:
#     """Agent intelligent orchestrant SQL et Recherche Sémantique."""
#     def __init__(self):
#         self.vsm = VectorStoreManager()
#         # self.client = AsyncInferenceClient(
#         #     model=HF_MODEL_NAME,
#         #     token=HF_API_KEY
#         # )
#         self.client = ChatMistralAI(
#             model_name=MODEL_NAME,
#             api_key=MISTRAL_API_KEY, #type:ignore
#             temperature=TEMPERATURE,
#             max_tokens=MAX_TOKENS,
#             top_p=TOP_P,
#             max_retries = 1
#         )
#         self.prompt_text = AGENT_SYSTEM_PROMPT_BEFORE

#     async def get_context_index(self, question: str) -> list:
#         """Récupère les documents dans l'index."""
#         try:
#             results = self.vsm.search(question, k=SEARCH_K)
#             return [res['text'] for res in results]
#         except Exception as e:
#             logger.error(f"Erreur lors de la recherche vectorielle : {e}")
#             return []

#     async def generate_response(self, question: str, contexts: list) -> str:
#         """Orchestre la réponse en consultant SQL et VectorStore en parallèle."""
#         logger.info(f"Traitement de la question : {question}...")

#         context_text = "\n\n".join([f"{context}" for context in contexts])
#         if not context_text:
#             logging.warning("Aucun document pertinents trouvé")
#             context_text = "Aucune information spécifique trouvée."

#         # Construire le prompt final pour l'API
#         full_system_content = self.prompt_text.format(
#         context_text=context_text,
#         question=question
#         )

#         # messages = [
#         #     {
#         #         "role": "system", 
#         #         "content": f"{self.prompt_text}."
#         #     },
#         #     {
#         #         "role": "user",
#         #         "content": f"CONTEXTE:\n{context_text}\n\nQUESTION: {question}"
#         #     }
#         # ]
#         messages = [
#             {
#                 "role": "system", 
#                 "content": full_system_content
#             }
#         ]

#         try:
#             logging.info(f"Appel à l'API modèle '{MODEL_NAME}'...")
#             # response = await self.client.chat_completion(
#             #     messages=messages,
#             #     max_tokens=MAX_TOKENS,
#             #     temperature=TEMPERATURE,
#             #     top_p = TOP_P,
#             #     stop=["</s>", "[/ASS]"] # Force l'arrêt (balises de folie)
#             # )
#             response = await self.client.ainvoke(messages)
#             # if response.choices and len(response.choices) > 0:
#                 # logging.info("Réponse reçue de l'API.")
#                 # return response.choices[0].message.content #type:ignore
#             if response.content and len(response.content) > 0:
#                 logging.info("Réponse reçue de l'API.")
#                 return response.content #type:ignore
#             else:
#                 logging.warning("L'API n'a pas retourné de choix valide.")
#                 return "Désolé, je n'ai pas pu générer de réponse valide."
#         except Exception as e:
#             logging.exception(f"Erreur API: {str(e)}")
#             return (
#                 "Je suis désolé, une erreur technique m'empêche de répondre."
#                 "Veuillez réessayer plus tard."
#             )


# livrable_p10/app/agents/nba_agent.py
import logging
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from livrable_p10.app.tools.sql.sql_pipeline import nlp_to_sql_pipeline
from livrable_p10.app.tools.semantic.vector_store import VectorStoreManager
from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
    TOP_P, TEMPERATURE, MAX_TOKENS,
    MISTRAL_API_KEY, BASE_URL, MODEL_NAME
)
from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT_AFTER, AGENT_FEW_SHOTS


logger = logging.getLogger(__name__)


# --- Modèles et Dépendances ---

class AgentDeps(BaseModel):
    """Dépendances lourdes, connexion DB, type pydantic non standard injectées dans l'agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True) # Pydantic ne stop pas VectorStoreManager
    vector_store: VectorStoreManager

# Note : Pour PydanticAI, on utilise l'URL du routeur sans le nom du modèle à la fin,
# car PydanticAI l'ajoutera lui-même dans la requête POST.

# 1. Création du Provider avec les paramètres Mistral
# On passe la base_url et l'api_key directement comme admis par ta signature
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
    }
)

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

# --- Outils (Tools) ---

@nba_agent.tool
# ctx est une obligation de signature. Même si tu ne l'utilises pas, Pydantic AI injecte toujours
# le contexte d'exécution (RunContext) comme premier argument de tes outils.
async def ask_database(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """Accès aux statistiques NBA (Points, moyennes, records)."""
    logging.info(f"Agent appelle SQL pour : {user_query}")
    return await nlp_to_sql_pipeline(user_query)

@nba_agent.tool
def ask_index(ctx: RunContext[AgentDeps], user_query: str) -> str:
    """Accès au contexte sémantique (Articles, histoire, avis)."""
    logging.info(f"Agent appelle index pour : {user_query}")
    results = ctx.deps.vector_store.search(user_query, k=SEARCH_K)
    if not results:
        return "Aucune archive textuelle trouvée pour cette question."
    formatted_results = [
        f"(Sujet: {result['metadata'].get('title', 'Sans titre')}) | {result['text']}"
        for result in results
    ]
    return "\n\n".join(formatted_results)


# ======================= Wrapper de session ==============================


# async def run_nba_assistant(user_query: str) -> str:
#     """
#     Pydantic AI décide seul d'utiliser ask_database, ask_index, ou les deux.
#     """
#     vsm = VectorStoreManager()
#     deps = AgentDeps(vector_store=vsm)

#     try:
#         # L'exécution de l'agent
#         result = await nba_agent.run(user_query, deps=deps)
#         # 1. Tentative Pydantic AI standard (version récente)
#         if hasattr(result, 'data'):
#             print("data")
#             return result.data
#         # 2. Tentative via l'attribut 'new_data' (certaines versions beta)
#         if hasattr(result, 'new_data'):
#             print("new_data")
#             return result.new_data
#         # 3. Récupération du dernier message de l'assistant (méthode universelle)
#         if hasattr(result, 'all_messages'):
#             print("all_messages")
#             last_msg = result.all_messages()[-1]
#             # Si c'est un ModelResponse
#             if hasattr(last_msg, 'parts'):
#                 print("parts")
#                 return last_msg.parts[0].content
#         # 4. Ultime secours : on renvoie l'objet tel quel
#         print("Ultime secours")
#         return str(result)

#     except Exception as e:
#         logging.error(f"Erreur Agent : {e}")
#         return f"Une erreur est survenue : {str(e)}"
class NBAEngine:
    def __init__(self):
        self.vsm = VectorStoreManager()
        self.deps = AgentDeps(vector_store=self.vsm)

    async def run_nba_assistant(self, question: str) -> str:
        """Exécute l'agent avec les dépendances déjà chargées."""
        try:
            # L'exécution de l'agent
            result = await nba_agent.run(question, deps=self.deps)
            # 1. Tentative Pydantic AI standard (version récente)
            if hasattr(result, 'data'):
                print("data")
                return result.data
            # 2. Tentative via l'attribut 'new_data' (certaines versions beta)
            if hasattr(result, 'new_data'):
                print("new_data")
                return result.new_data
            # 3. Récupération du dernier message de l'assistant (méthode universelle)
            if hasattr(result, 'all_messages'):
                print("all_messages")
                last_msg = result.all_messages()[-1]
                # Si c'est un ModelResponse
                if hasattr(last_msg, 'parts'):
                    print("parts")
                    return last_msg.parts[0].content
            # 4. Ultime secours : on renvoie l'objet tel quel
            print("Ultime secours")
            return str(result)

        except Exception as e:
            logging.error(f"Erreur Agent : {e}")
            # return f"Une erreur est survenue : {str(e)}"
            raise RuntimeError(f"L'agent n'a pas pu répondre : {e}")

    async def get_eval_data(self, question: str) -> dict:
        """
        Méthode dédiée pour l'évaluation RAGAS.
        Retourne la réponse ET les contextes extraits.
        """
        # 
        contexts = [result['text'] for result in self.vsm.search(question, k=SEARCH_K)]
        answer = await self.run_nba_assistant(question)
        return {
            "answer": answer,
            "contexts": contexts
        }