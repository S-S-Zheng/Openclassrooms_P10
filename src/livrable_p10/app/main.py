"""
Ce module contient la classe NBAEngine. Elle est autonome et asynchrone (pour Ragas),
mais on peut l'utiliser de manière synchrone pour Streamlit.
"""

# NBAAgent.py
import streamlit as st
import asyncio
import logfire
import logging


from livrable_p10.app.utils.config import APP_TITLE, HF_MODEL_NAME, NAME
from livrable_p10.app.agents.nba_agent import NBAEngine


# =================== Configuration logs ===================
logging.basicConfig(level=logging.INFO)
logfire.configure()
logfire.instrument_pydantic_ai()

# =================== Initialisation des ressources ===================
@st.cache_resource
def get_engine():
    return NBAEngine() # Charge tout en mémoire

engine = get_engine()

# =================== UI Streamlit ===================
st.set_page_config(page_title=APP_TITLE)
st.title(APP_TITLE)
st.caption(f"Assistant virtuel pour {NAME} | Modèle: {HF_MODEL_NAME}")

# =================== Initialisation de l'historique de conversation ===================
if "messages" not in st.session_state:
    # Message d'accueil initial
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"Bonjour ! Je suis votre analyste IA pour la {NAME}. Posez-moi vos questions sur"
            "les équipes, les joueurs ou les statistiques, et je vous répondrai en me basant"
            "sur les données les plus récentes."
        )
    }]
# =================== Affichage historique ===================
for msg in st.session_state.messages: # Maintient la mémoire de la session
    with st.chat_message(msg["role"]): # Gère l'affichage des bulels de messages
        st.markdown(msg["content"])

# =================== Zone de saisie utilisateur ===================
if prompt := st.chat_input(f"Posez votre question sur la {NAME}..."):
    # 1. Ajouter et afficher le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Afficher indicateur + Générer la réponse de l'assistant via LLM
    with st.chat_message("assistant"):
        with st.spinner("Consultation des archives..."):
            # # ------ Retrieve
            # # On utilise asyncio.run pour faire le pont entre l'UI synchrone et l'engine async
            # contexts = asyncio.run(engine.get_context_index(prompt))
            # # ------- Générate
            # # Génération de la réponse de l'assistant en utilisant le prompt augmenté
            # full_response = asyncio.run(engine.generate_response(prompt, contexts))
            # Appel asynchrone à l'Engine (Agent Pydantic AI)
            full_response = asyncio.run(engine.run_nba_assistant(prompt))
            
            # Ajouter la réponse de l'assistant à l'historique (pour affichage UI)
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})