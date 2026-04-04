"""
Les forums et spécialement Reddit ici sont largement pollué par divers sources de bruits:

* **Les menus et boutons**: "Répondre", "Sponsorisé", "Accéder au contenu principal"
    polluent le texte.
* **La mise en page en colonnes**: L'OCR lit parfois de gauche à droite sans comprendre
    que ce sont des blocs séparés, mélangeant les commentaires.
* **Le texte inutile**: Les dates ("12/06/2025"), les scores de vote ("356"), et les pubs.

De plus, les méthodes de scanning ou d'OCR peuvent rajouter du bruit comme les hallucinations
sur une lettre au lieu d'une autre, les espacements, les mélanges de contexte...

Le nettoyage de l'ensemble des bruits est alors quasiment impossible via un code léger, cependant
on peut tout de même grandement améliorer la qualté du document transmis et le LLM e chargera
d'ignorer les bruits restants. Et en cas d'insatisfaction, des méthodes complémentaires au niveau
du LLM peuvent être ajouté afin d'améliorer la qualité de réponse.
"""
# Imports
import os
import re
import logging
from typing import List,Dict,Any

logger = logging.getLogger(__name__)
# ==============================================================


def get_clean_and_entitle(
    documents:List[Dict[str, Any]],
    blacklist_path:str="blacklist.txt"
)->List[Dict[str, Any]]:
    """
    Nettoye le document avant le chunking. On réorganise le ``page_content`` en parcourant
    les lignes du document:
    * Si un terme dans la blacklist se retrouve dans la ligne, on ignore la ligne.
    * Si un caractère non existant dans la langue anglaise, la ligne est ignorée.

    Une fois sortie du document, on va chercher le titre via un terme a retrouver.

    Args:
        documents (List[Dict[str, Any]]): Document à traiter
        blacklist_path (str): Chemin du fichier de blacklisting. par défaut "blacklist.txt"

    Returns:
        List[Dict[str, Any]]: Document après nettoyage
    """
    # Charge la blacklist en un set
    logging.info("Chargement du fichier blacklist.txt")
    if os.path.exists(blacklist_path):
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            blacklist = {line.strip().lower() for line in f if line.strip()}
    else:
        logging.warning("Pas de fichier ``blacklist.txt`` trouvé...")
        blacklist = set()

    for doc in documents:
        logging.info("Nettoyage des documents en cours...")
        # On créée une liste des lignes qui composent le document via le séparateur \n
        lines = doc['page_content'].split('\n')
        # Le titre est dans le header de la page en deuxième ligne (normalement)
        title = lines[1].strip()
        # OU ALORS LA 11è ligne (si la seconde est vraiment cropée par ...)
        # autor_badge = " ".join(lines[8:15]).lower()
        # title = lines[10].strip() if "top 1%" in autor_badge else lines[11].strip()
        # La copie nettoyée
        cleaned_lines = []

        for line in lines:
            l_strip = line.strip()
            if not l_strip: # Si la ligne est juste composé d'espaces
                continue
            l_lower = l_strip.lower()

            # ----------- FILTRE BLACKLIST
            # On ignore si la ligne est dans la blacklist
            if l_lower in blacklist:
                continue
            # On ignore les lignes de "métadonnées" Reddit (ex: "-15 j", "~ 2 h", "356")
            if re.match(r'^[\d\s\+\-~]+$', l_strip) or re.search(r'\d+\s*[jmh]$', l_strip):
                continue
            # ----------- FILTRE DES ACCENTS
            # Si la ligne contient é, è, à, ç, ô on ignore (Les pubs et UI de Reddit sont en FR)
            if re.search(r'[éèàçô]', l_strip):
                continue
            # ----------- ARRÊT PRÉMATURÉ DU DOCUMENT
            if "afficher plus de commentaires" in l_lower:
                break

            # Si la ligne a survécu, on la garde
            cleaned_lines.append(l_strip)

        # # DÉTECTION DU TITRE
        # title_ref = "rechercher dans r/nba"
        # title = lines[3].strip()
        # try:
        #     # Trouver l'index de la référence qui va nous servir a retrouver le titre
        #     ref_index = next(
        #         index for index, text in enumerate(cleaned_lines)
        #         if text.lower() == title_ref
        #     )
        #     # On prend le 2ème élément après la réf (Index + 2 = 2ème)
        #     potential_title_idx = ref_index + 2
        #     if potential_title_idx < len(cleaned_lines):
        #         title = cleaned_lines[potential_title_idx]
        #     # On supprime la réf de la liste finale
        #     final_content_lines = [
        #         line for line in cleaned_lines
        #         if line.lower() != title_ref
        #     ]
        # except StopIteration:
        #     # Si la réf n'a pas été trouvée, on garde tout
        #     final_content_lines = cleaned_lines

        # ASSEMBLAGE FINALE
        # doc['page_content'] = f"Sujet: {title}\n\n" + "\n".join(final_content_lines)
        doc['page_content'] = "\n".join(cleaned_lines)
        doc['metadata']["title"] = title

    return documents