"""
Module principal de l'application Streamlit.

Ce module gère l'interface utilisateur, la gestion de la session de chat,
et l'orchestration entre l'interface synchrone de Streamlit et le moteur
asynchrone NBAEngine.

Important
-----
Pour le lancer: streamlit run chemin/vers/main.py
"""

import os
import warnings

# Bloque les warnings de dépréciation (LambdaRuntimeClient)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="Accessing LambdaRuntimeClient")
# Réduit le niveau de log de Transformers
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
# ATTENTION on cache juste car spamming de warning dû a transformers + answer_relevancy mais
# mais il y a dépréciation donc potentiel crash futur...

import streamlit as st
import asyncio
import logfire
import logging


from livrable_p10.app.utils.config import APP_TITLE, NAME, MODEL_NAME
from livrable_p10.app.agents.nba_agent import NBAEngine


# =============================================================================
# CONFIGURATION DE LA PAGE (Doit être la première commande Streamlit)
# ATTENTION OBLIGATOIREMENT JUSTE APRÈS LES IMPORTS!
st.set_page_config(
    page_title=APP_TITLE,
    layout="centered", # ou "wide"
    initial_sidebar_state="auto"
)


# =========================================================
# LOGS ET RESSOURCES
# =================== Configuration logs ===================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# Initialise la connexion avec les serveurs de Logfire
logfire.configure()
# Permet de suivre le cheminement de pensée de l'Agent
logfire.instrument_pydantic_ai()

# =================== Initialisation des ressources ===================
@st.cache_resource
def get_engine():
    return NBAEngine() # Charge tout en mémoire

engine = get_engine()

# =====================================================
# INTERFACE UTILISATEUR (UI)
# =================== Initialisation de l'historique de conversation ===================
st.title(APP_TITLE)
st.caption(f"Assistant virtuel pour {NAME} | Modèle: {MODEL_NAME}")

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

# ============================================================================
# INTERACTION CHAT
# =================== Zone de saisie utilisateur ===================
if prompt := st.chat_input(f"Posez votre question sur la {NAME}..."):
    # Ajouter et afficher le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Afficher indicateur + Générer la réponse de l'assistant via LLM
    with st.chat_message("assistant"):
        with st.spinner("Consultation des archives..."):
            try:
                # --- Gestion de la boucle d'événements asynchrones ---
                # Streamlit gérant son propre contexte, nous devons récupérer ou créer
                # une boucle d'événements pour exécuter l'appel asynchrone à l'agent.
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Appel asynchrone à l'Engine (Agent Pydantic AI)
                # asyncio.run() peut parfois lever une erreur RuntimeError dans Streamlit car
                # il gère lui même les cntextes asynchrones
                full_response = loop.run_until_complete(engine.run_nba_assistant(prompt))

                # Ajouter la réponse de l'assistant à l'historique (pour affichage UI)
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Désolé, une erreur technique est survenue : {e}")