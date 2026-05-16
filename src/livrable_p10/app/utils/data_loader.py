"""
Module de récupération des sources et constitution d'une liste de dictionnaire pour indexation.\n
Plusieurs fonctions de récupération sont implémenter et suivant le besoin, la fonction en question
est appelée, a noté que pour les pdf, on tente une approche standard avec ``PyPDF2`` et un fallback
sur EasyOCR si echec. Après récupération, une standardisation de la
source est réalisée sous la forme d'une liste de dictionnaire avec deux clées: ``page_content`` qui
contient la source contextuelle et ``metadata`` qui est un sous-dictionnaire contenant
les métadonnées de la source.

Workflow
--------
* Le dossier cible est scanné récursivement (ou un zip est téléchargé depuis une url).
* On dirige ensuite le fichier vers la fonction de récupération en charge (pdf, docx, txt) via
    un identificateur sur le suffixe du fichier.
* On engage l'extraction et dans le cas du pdf on tente d'abord avec ``PyPDF2`` sinon EasyOCR.
* On standardise le texte en un dictionnaire composé de ``page_content`` et de métadonnés
    ``metadata``. L'ensemble des dictionnaires est concaténé dans une liste.

IMPORTANT
--------
* On a retiré les traitements sur sources tabulaire (csv et excel) puisque les méthodes ne sont
    pas adaptés. Les excel seront traités par la base de donnée (``load_excel_to_db.py``)
* Fait partie du groupe de fichiers fourni
"""

# Imports
import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from tqdm import tqdm  # Ajout de tqdm

logger = logging.getLogger(__name__)


# ===========================================================


# --- Importations pour OCR ---
try:
    import easyocr
    import fitz  # PyMuPDF
    from PIL import Image

    # Initialiser le lecteur EasyOCR une seule fois
    logging.info("Initialisation du lecteur EasyOCR...")
    reader = easyocr.Reader(["en", "fr"])
    logging.info("Lecteur EasyOCR initialisé.")

except ImportError as e:
    logging.warning(
        f"Modules OCR (PyMuPDF, Pillow, easyocr) non installés ou erreur: {e}."
        "L'OCR pour PDF ne sera pas disponible."
    )
    fitz = None
    Image = None
    easyocr = None
    reader = None
except Exception as e:
    logging.error(f"Erreur inattendue lors du chargement des modules/modèle OCR: {e}")
    fitz = None
    Image = None
    easyocr = None
    reader = None


# --- Fonctions d'extraction de texte ---


def extract_text_from_pdf_with_ocr(file_path: str) -> Optional[str]:
    """Extrait le texte d'un fichier PDF en utilisant l'OCR (EasyOCR)."""
    if not fitz or not reader:
        logging.warning("Modules/Modèle OCR non disponibles. Impossible d'effectuer l'OCR.")
        return None

    text_content = []
    try:
        doc = fitz.open(file_path)
        # Utiliser tqdm pour la barre de progression
        for page_num in tqdm(range(len(doc)), desc=f"OCR de {os.path.basename(file_path)}"):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Augmenter la résolution pour l'OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # type:ignore

            try:
                img_np = np.array(img)
                results = reader.readtext(img_np)
                page_text = "\n".join([res[1] for res in results])  # type:ignore
                text_content.append(page_text)
                # logging.info(f"OCR effectuée sur la page {page_num + 1} de {file_path}
                # avec EasyOCR") # Commenté pour éviter le spam de logs avec tqdm
            except Exception as ocr_e:
                logging.error(
                    f"Erreur lors de l'OCR de la page {page_num + 1} de {file_path}"
                    f"avec EasyOCR: {ocr_e}"
                )
                continue

        doc.close()
        full_text = "\n".join(text_content).strip()
        if full_text:
            logging.info(f"Texte extrait via OCR de PDF: {file_path} ({len(full_text)} caractères)")
            return full_text
        else:
            logging.warning(f"Aucun texte significatif extrait via OCR de {file_path}.")
            return None
    except Exception as e:
        logging.error(f"Erreur lors de l'ouverture ou du traitement OCR du PDF {file_path}: {e}")
        return None


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extrait le texte d'un PDF avec un fallback vers l'OCR.

    Args:
        file_path: Chemin absolu ou relatif vers le fichier PDF.

    Returns:
        Le texte extrait ou None en cas d'échec total.
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        text = "".join(page.extract_text() + "\n" for page in reader.pages if page.extract_text())

        if len(text.strip()) < 100:  # Si très peu de texte est extrait, tenter l'OCR
            logging.info(
                f"Peu de texte trouvé dans {file_path} via extraction standard"
                f"({len(text.strip())} caractères). Tentative d'OCR..."
            )
            ocr_text = extract_text_from_pdf_with_ocr(file_path)
            if ocr_text:
                return ocr_text
            else:
                logging.warning(
                    f"L'OCR n'a pas non plus produit de texte significatif pour {file_path}."
                )
                return text  # Retourne le peu de texte trouvé ou vide

        logging.info(f"Texte extrait de PDF: {file_path} ({len(text)} caractères)")
        return text
    except Exception as e:
        logging.error(
            f"Erreur extraction PDF {file_path}: {e}. Tentative d'OCR en dernier recours..."
        )
        # Si l'extraction standard échoue complètement, tenter l'OCR
        ocr_text = extract_text_from_pdf_with_ocr(file_path)
        if ocr_text:
            return ocr_text
        else:
            logging.warning(
                "L'OCR n'a pas non plus produit de texte significatif après échec"
                f"de l'extraction standard pour {file_path}."
            )
            return None


def extract_text_from_docx(file_path: str) -> Optional[str]:
    """Extrait le texte d'un fichier Word DOCX."""
    try:
        import docx

        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs if para.text)
        logging.info(f"Texte extrait de DOCX: {file_path} ({len(text)} caractères)")
        return text
    except Exception as e:
        logging.error(f"Erreur extraction DOCX {file_path}: {e}")
        return None


def extract_text_from_txt(file_path: str) -> Optional[str]:
    """Extrait le texte d'un fichier texte brut."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        logging.info(f"Texte extrait de TXT: {file_path} ({len(text)} caractères)")
        return text
    except Exception as e:
        logging.error(f"Erreur extraction TXT {file_path}: {e}")
        return None


# --- Fonctions de chargement ---


def download_and_extract_zip(url: str, output_dir: str) -> bool:
    """Télécharge un fichier ZIP depuis une URL et l'extrait."""
    if not url:
        logging.warning("Aucune URL fournie pour le téléchargement.")
        return False
    try:
        logging.info(f"Téléchargement des données depuis {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            logging.info(f"Extraction du contenu dans {output_dir}...")
            z.extractall(output_dir)
        logging.info("Téléchargement et extraction terminés.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de téléchargement: {e}")
        return False
    except zipfile.BadZipFile:
        logging.error("Le fichier téléchargé n'est pas un ZIP valide.")
        return False
    except Exception as e:
        logging.error(f"Erreur inattendue lors du téléchargement/extraction: {e}")
        return False


def load_and_parse_files(input_dir: str) -> List[Dict[str, Any]]:
    """
    Charge et transforme tous les fichiers d'un répertoire en documents standardisés.\n
    Cette fonction est le point d'entrée principal de la phase 'Extract' de l'ETL.
    Elle gère la récursivité et l'attribution des métadonnées de source.

    Args:
        input_dir: Le chemin du répertoire contenant les données brutes.

    Returns:
        Une liste de dictionnaires au format {'page_content': str, 'metadata': dict}
    """
    documents: List[Dict[str, Any]] = []
    input_path = Path(input_dir)
    if not input_path.is_dir():
        logging.error(f"Le répertoire d'entrée '{input_dir}' n'existe pas.")
        return []

    logging.info(f"Parcours du répertoire source: {input_dir}")
    for file_path in input_path.rglob("*.*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(input_path)
            source_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
            ext = file_path.suffix.lower()

            logging.debug(
                f"Traitement du fichier: {relative_path} (Dossier source: {source_folder})"
            )

            extracted_content = None
            if ext == ".pdf":
                extracted_content = extract_text_from_pdf(str(file_path))
            elif ext == ".docx":
                extracted_content = extract_text_from_docx(str(file_path))
            elif ext == ".txt":
                extracted_content = extract_text_from_txt(str(file_path))
            else:
                logging.warning(f"Type de fichier non supporté ignoré: {relative_path}")
                continue

            if not extracted_content:
                logging.warning(f"Aucun contenu n'a pu être extrait de {relative_path}")
                continue

            documents.append(
                {
                    "page_content": extracted_content,
                    "metadata": {
                        "source": str(relative_path),
                        "filename": file_path.name,
                        "category": source_folder,
                        "full_path": str(file_path.resolve()),
                    },
                }
            )

    logging.info(f"{len(documents)} documents chargés et parsés.")
    return documents
