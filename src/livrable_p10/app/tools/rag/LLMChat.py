

# livrable_p10/app/tools/rag/LLMChat.py
import logging
from huggingface_hub import AsyncInferenceClient
from openai import AsyncOpenAI
from langchain_mistralai import ChatMistralAI

from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
    TOP_P, TEMPERATURE, MAX_TOKENS,
    MISTRAL_API_KEY, BASE_URL, MODEL_NAME
)
from livrable_p10.app.tools.rag.vector_store import VectorStoreManager
from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT_BEFORE

logger = logging.getLogger(__name__)


# ============================================================


class LLMChat:
    """LLM du RAG ."""
    
    def __init__(self):
        self.vsm = VectorStoreManager()
        # self.client = AsyncInferenceClient(
        #     model=HF_MODEL_NAME,
        #     token=HF_API_KEY
        # )
        self.client = ChatMistralAI(
            model_name=MODEL_NAME,
            api_key=MISTRAL_API_KEY, #type:ignore
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
            max_retries = 1
        )
        self.prompt_text = AGENT_SYSTEM_PROMPT_BEFORE

    async def get_context(self, question: str) -> list:
        """Récupère les documents pertinents."""
        try:
            results = self.vsm.search(question, k=SEARCH_K)
            return [res['text'] for res in results]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle : {e}")
            return []

    async def generate_response(self, question: str, contexts: list) -> str:
        """Génère une réponse basée sur le contexte fourni."""
        context_text = "\n\n".join([f"{context}" for context in contexts])
        if not context_text:
            logging.warning("Aucun document pertinents trouvé")
            context_text = "Aucune information spécifique trouvée."

        # Construire le prompt final pour l'API
        full_system_content = self.prompt_text.format(
        context_text=context_text,
        question=question
        )

        # messages = [
        #     {
        #         "role": "system", 
        #         "content": f"{self.prompt_text}."
        #     },
        #     {
        #         "role": "user",
        #         "content": f"CONTEXTE:\n{context_text}\n\nQUESTION: {question}"
        #     }
        # ]
        messages = [
            {
                "role": "system", 
                "content": full_system_content
            }
        ]

        try:
            logging.info(f"Appel à l'API modèle '{MODEL_NAME}'...")
            # response = await self.client.chat_completion(
            #     messages=messages,
            #     max_tokens=MAX_TOKENS,
            #     temperature=TEMPERATURE,
            #     top_p = TOP_P,
            #     stop=["</s>", "[/ASS]"] # Force l'arrêt (balises de folie)
            # )
            response = await self.client.ainvoke(messages)
            # if response.choices and len(response.choices) > 0:
                # logging.info("Réponse reçue de l'API.")
                # return response.choices[0].message.content #type:ignore
            if response.content and len(response.content) > 0:
                logging.info("Réponse reçue de l'API.")
                return response.content #type:ignore
            else:
                logging.warning("L'API n'a pas retourné de choix valide.")
                return "Désolé, je n'ai pas pu générer de réponse valide."
        except Exception as e:
            logging.exception(f"Erreur API: {str(e)}")
            return (
                "Je suis désolé, une erreur technique m'empêche de répondre."
                "Veuillez réessayer plus tard."
            )