

# livrable_p10/app/tools/rag/LLMChat.py
import logging
from huggingface_hub import AsyncInferenceClient


from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
    TOP_P, TEMPERATURE, MAX_TOKENS
)
from livrable_p10.app.tools.rag.vector_store import VectorStoreManager
from livrable_p10.app.utils.prompts import AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# ============================================================


class LLMChat:
    """LLM du RAG ."""
    
    def __init__(self):
        self.vsm = VectorStoreManager()
        self.client = AsyncInferenceClient(
            model=HF_MODEL_NAME,
            provider="hf-inference",
            timeout=20.0,
            token=HF_API_KEY
        )
        self.prompt_text = AGENT_SYSTEM_PROMPT

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
        context_text = "\n\n".join([f"--- Details ---\n{context}" for context in contexts])
        if not context_text:
            logging.warning("Aucun document pertinents trouvé")
            context_text = "Aucune information spécifique trouvée."

        messages = [
            {
                "role": "system", 
                "content": f"{self.prompt_text}.\n\nCONTEXTE:\n{context_text}"
            },
            {"role": "user", "content": question}
        ]

        try:
            logging.info(f"Appel à l'API modèle '{HF_MODEL_NAME}'...")
            response = await self.client.chat_completion(
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p = TOP_P
            )
            if response.choices and len(response.choices) > 0:
                logging.info("Réponse reçue de l'API.")
                return response.choices[0].message.content #type:ignore
            else:
                logging.warning("L'API n'a pas retourné de choix valide.")
                return "Désolé, je n'ai pas pu générer de réponse valide."
        except Exception as e:
            logging.exception(f"Erreur API: {str(e)}")
            return (
                "Je suis désolé, une erreur technique m'empêche de répondre."
                "Veuillez réessayer plus tard."
            )