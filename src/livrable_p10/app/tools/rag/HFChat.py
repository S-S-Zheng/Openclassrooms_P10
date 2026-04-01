# HFChat.py (Version RAG optimisée pour Hugging Face Free API)
import streamlit as st
import os
import logging
import asyncio
from huggingface_hub import InferenceClient
from typing import Dict, List

# --- Importations depuis vos modules ---
try:
    from livrable_p10.app.utils.config import (
        HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
        APP_TITLE, NAME
    )
    from livrable_p10.app.tools.rag.vector_store import VectorStoreManager
except ImportError as e:
    st.error(f"Erreur d'importation: {e}. Vérifiez votre fichier config.py.")
    st.stop()

# --- Configuration du Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# --- Initialisation du Client Hugging Face ---
# On utilise InferenceClient : pas besoin de base_url complexe, il connaît les routes.
@st.cache_resource
def get_hf_client():
    if not HF_API_KEY:
        st.error("Token HF_API_KEY manquant dans le .env")
        st.stop()
    return InferenceClient(model=HF_MODEL_NAME, token=HF_API_KEY)

client = get_hf_client()

# --- Chargement du Vector Store ---
@st.cache_resource
def get_vector_store_manager():
    try:
        # Le VectorStoreManager utilise HuggingFaceInferenceAPIEmbeddings (LangChain)
        # qui est compatible avec ton token.
        return VectorStoreManager()
    except Exception as e:
        st.error(f"Erreur base de connaissances : {e}")
        return None

vsm = get_vector_store_manager()

# --- Logique de l'Interface ---
st.set_page_config(page_title=APP_TITLE)
st.title(APP_TITLE)
st.caption(f"Propulsé par {HF_MODEL_NAME} (Inference API)")

# Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Traitement de la question ---
if prompt := st.chat_input("Posez votre question sur la NBA..."):
    # 1. Afficher le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. RAG : Recherche de contexte
    with st.spinner("Consultation des archives NBA..."):
        context_text = ""
        if vsm:
            results = vsm.search(prompt, k=SEARCH_K)
            context_text = "\n\n".join([f"--- Archive ---\n{r['text']}" for r in results])
        
        if not context_text:
            context_text = "Aucune information spécifique trouvée dans les archives."

    # 3. Génération de la réponse
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Construction du prompt pour l'Instruct Model
        # On respecte le format de chat standard
        messages = [
            {
                "role": "system", 
                "content": (
                    "Tu es un expert NBA. Réponds en utilisant le contexte fourni"
                    f"ci-dessous.\n\nCONTEXTE:\n{context_text}"
                )
            },
            {"role": "user", "content": prompt}
        ]

        try:
            # Utilisation de chat_completion (synchrone ici pour simplifier avec Streamlit)
            # C'est plus stable que l'async dans un contexte de script Streamlit linéaire
            response = client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.2,
                stream=False # On peut passer en True pour un effet de frappe plus tard
            )
            
            full_response = response.choices[0].message.content
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            error_msg = f"Désolé, une erreur API est survenue : {str(e)}"
            st.error(error_msg)
            full_response = error_msg

    st.session_state.messages.append({"role": "assistant", "content": full_response})