

# tests/test_agent.py
import asyncio
import logfire

import sys

from livrable_p10.app.main import run_nba_assistant

# On active logfire pour voir les "thoughts" de l'agent en live
logfire.configure()

async def debug_agent():
    queries = [
        # Test 1 : Pur SQL (Quantitatif)
        "Qui est le meilleur marqueur de l'équipe sur toute la saison ?",
        
        # Test 2 : Pur RAG (Qualitatif / Reddit)
        "Que disent les fans de l'ambiance au Madison Square Garden ?",
        
        # Test 3 : Hybride (Demande une réflexion)
        "Compare les stats de Curry avec ce que les gens pensent de sa forme actuelle."
    ]

    for q in queries:
        print(f"\n🚀 Question: {q}")
        try:
            # La réponse est maintenant un simple string
            response_text = await run_nba_assistant(q)
            print(f"🤖 Réponse: {response_text}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent())