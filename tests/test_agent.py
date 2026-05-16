import os
import warnings

# Bloque les warnings de dépréciation (LambdaRuntimeClient)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="Accessing LambdaRuntimeClient")
# Réduit le niveau de log de Transformers
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
# ATTENTION on cache juste car spamming de warning dû a transformers + answer_relevancy mais
# mais il y a dépréciation donc potentiel crash futur...

# tests/test_agent.py
import asyncio  # noqa: E402
import logging  # noqa: E402

import logfire  # noqa: E402

# from old.main import run_nba_assistant
from livrable_p10.app.agents.nba_agent import NBAEngine  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# On active logfire les étapes de l'agent
logfire.configure()
logfire.instrument_pydantic_ai()

# =================================================================


async def test_rag():
    queries = [
        # Test 1 : Pur SQL (Quantitatif)
        "Qui est le meilleur scorer sur toute la saison ?",
        # Test 2 : Pur RAG (Qualitatif / Reddit)
        "Y'a-t'il un match qui pourrait ennuyer les spectateurs ?",
        # Test 3 : Hybride (Demande une réflexion)
        """
        Qui est le meilleur joueur selon les internautes?
        Compare le en terme de point avec le meilleur joueur de la saison.
        """,
    ]

    engine = NBAEngine()

    for i, q in enumerate(queries):
        print(f"\n[{i + 1}/{len(queries)}] Question: {q}")
        try:
            # On lance l'agent
            response_text = await engine.run_nba_assistant(q)
            print(f"Réponse: {response_text}")
        except Exception as e:
            print(f"Erreur sur la question {i + 1}: {e}")

        # "Ralentir" l'asynchrone
        if i < len(queries) - 1:
            print("Attente entre les questions pour éviter le code 429")
            await asyncio.sleep(10.0)


if __name__ == "__main__":
    asyncio.run(test_rag())
