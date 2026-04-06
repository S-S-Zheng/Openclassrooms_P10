

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine

from livrable_p10.app.tools.sql.sql_tool import SQLQueryEngine
from livrable_p10.app.utils.prompts import SQL_SYSTEM_PROMPT, SQL_FEW_SHOT
from livrable_p10.app.utils.config import (
    HF_API_KEY, HF_MODEL_NAME, SEARCH_K,
    TOP_P, TEMPERATURE, MAX_TOKENS,
    MISTRAL_API_KEY, BASE_URL, MODEL_NAME,
    DATABASE_URL
)


# Configuration du logger
logger = logging.getLogger(__name__)


# ========================== Helper de rapport ============================
def _write_report(service, query, sql, status, start_tick):
    """Insertion synchrone dans la table reports."""
    duration = int((time.monotonic() - start_tick) * 1000)
    try:
        with service.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO reports (created_at, user_query, sql_generated,
                    status_code, response_time_ms)
                    VALUES (:now, :query, :sql, :status, :time)
                """),
                {
                    "now": datetime.now().isoformat(),
                    "query": query,
                    "sql": sql,
                    "status": status,
                    "time": duration
                }
            )
    except Exception as e:
        logger.error(f"Erreur écriture report : {e}")

# ===============================================================

async def nlp_to_sql_pipeline(query: str) -> str:
    """Pipeline Tool pour l'Agent NBA avec logging automatique."""
    logging.info("Lancement du tool SQL...")
    start_time = time.monotonic()
    # Instanciation dynamique du service
    service = SQLQueryEngine(DATABASE_URL)

    sql_generated = "N/A"
    status = "INIT"

    try:
        # génère le sql à partir de la requete nlp
        sql = await service.generate_sql(query)
        if not sql:
            # Cas où le LLM ne renvoie rien ou échoue
            status = "SQL_GEN_FAILED_500"
            return "Désolé, je n'ai pas pu traduire votre demande en requête SQL."

        # lance la requete sql sur la db
        data = service.execute_query(sql)
        status = "SUCCESS_200"

        # Report
        _write_report(service, query, sql_generated, status, start_time)
        if not data:
            return (
                f"La requête a fonctionné ({sql_generated}) mais la base de"
                "données est muette pour cette recherche."
            )
        return f"Résultats SQL :\n{data}"

    except PermissionError:
        # Si _clean_sql_response a détecté un mot interdit (DROP, etc.)
        status = "FORBIDDEN_403"
        _write_report(service, query, sql_generated, status, start_time)
        return "Sécurité : Cette requête contient des commandes non autorisées."

    except Exception as e:
        # Erreur système imprévue (Type 500)
        status = "INTERNAL_ERROR_500"
        _write_report(service, query, sql_generated, status, start_time)
        logger.error(f"Crash tool SQL : {e}")
        return "Une erreur interne est survenue lors de l'accès aux données."