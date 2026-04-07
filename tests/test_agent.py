

# tests/test_agent.py
import logging
import asyncio
import logfire


# from old.main import run_nba_assistant
from livrable_p10.app.agents.nba_agent import NBAEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# On active logfire les étapes de l'agent
logfire.configure()
logfire.instrument_pydantic_ai()

async def debug_agent():
    queries = [
        # Test 1 : Pur SQL (Quantitatif)
        "Qui est le meilleur scorer sur toute la saison ?",

        # Test 2 : Pur RAG (Qualitatif / Reddit)
        "Que disent les fans à propos de Reggie Miller ?",

        # Test 3 : Hybride (Demande une réflexion)
        """
        Qui est le meilleur joueur selon les internautes? Compare le en terme de points
        avec le meilleur joueur de la saison.
        """
    ]

    engine = NBAEngine()

    for q in queries:
        print(f"\n Question: {q}")
        try:
            # La réponse est maintenant un simple string
            response_text = await engine.run_nba_assistant(q)
            print(f"Réponse: {response_text}")
        except Exception as e:
            print(f"Erreur : {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent())