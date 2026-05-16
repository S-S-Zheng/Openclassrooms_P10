"""
Pipeline de traitement Natural Language to SQL.

Ce module fait le pont entre la question brute de l'utilisateur et le moteur SQL.
Il gère l'orchestration, la journalisation (reporting) et la gestion des erreurs
métier (données manquantes, permissions).
"""

# Imports
import logging
import time

from sqlalchemy import text

from livrable_p10.app.tools.sql.sql_tool import SQLQueryEngine
from livrable_p10.app.utils.config import DATABASE_URL
from livrable_p10.app.utils.schemas import ReportInpuSchema

# Configuration du logger
logger = logging.getLogger(__name__)


# ========================== Helper de rapport ============================
def _write_report(service, query, sql, status, start_tick):
    """
    Monitore de manière synchrone les métadonnées de la requête.

    Args:
        service: Instance du moteur SQL pour accéder à la connexion.
        query: Question originale de l'utilisateur.
        sql: Requête SQL générée (ou "N/A").
        status: Code de statut final (ex: SUCCESS_200, FORBIDDEN_403).
        start_tick: Timestamp de début pour calculer la durée.
    """
    duration = int((time.monotonic() - start_tick) * 1000)
    try:
        # Check up Pydantic
        report_data = ReportInpuSchema(
            user_query=query, sql_generated=sql, status_code=status, response_time_ms=duration
        )
        with service.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO reports (user_query, sql_generated, status_code, response_time_ms)
                    VALUES (:user_query, :sql_generated, :status_code, :response_time_ms)
                """),
                report_data.model_dump(),  # Convertit l'objet Pydantic en dict
            )
    except Exception as e:
        logger.error(f"Erreur écriture report : {e}")


# ===============================================================


async def nlp_to_sql_pipeline(query: str) -> str:
    """
    Pipeline principal transformant une question en données statistiques.\n
    Cette fonction orchestre la génération SQL, l'exécution en base et
    le reporting systématique du succès ou de l'échec.

    Args:
        query: Question de l'utilisateur relative aux statistiques NBA.

    Returns:
        str: Message formaté contenant les résultats ou l'explication de l'erreur.
    """
    logging.info(f"Lancement du tool SQL concernant: {query}")
    start_time = time.monotonic()

    # Instanciation dynamique du service
    service = SQLQueryEngine(DATABASE_URL)
    sql_generated = "N/A"
    status = "INIT"

    try:
        # génère le sql à partir de la requete nlp
        sql_generated = await service.generate_sql(query)

        # Vérification des cas d'échec de génération ou d'absence de données
        if not sql_generated or "DATA_NOT_AVAILABLE" in sql_generated:
            status = "SQL_GEN_FAILED_500"
            # Report
            _write_report(service, query, sql_generated, status, start_time)
            return (
                f"Echec de la requete sql: {status}. L'outil SQL ne peut pas répondre"
                "à cette question, essayez l'index."
            )

        # lance la requete sql sur la db
        data = service.execute_query(sql_generated)
        status = "SUCCESS_200"
        # Report
        _write_report(service, query, sql_generated, status, start_time)

        # Si SUCCESS_200 mais retour vide
        if not data:
            return (
                f"La requête a fonctionné ({sql_generated}) mais rien n'a été trouvé."
                "Essayez l'index"
            )
        return f"Résultats SQL :\n{data}"

    except PermissionError:
        # Si _clean_sql_response a détecté un mot interdit (DROP, etc.)
        status = "FORBIDDEN_403"
        _write_report(service, query, sql_generated, status, start_time)
        return f"Commande non autorisée : {status}"

    except Exception as e:
        # Erreur système imprévue (Type 500)
        status = "INTERNAL_ERROR_500"
        _write_report(service, query, sql_generated, status, start_time)
        logger.error(f"Crash tool SQL : {e}")
        return (
            f"Erreur interne SQL ({status}). Les données statistiques ne sont pas accessibles"
            "pour cette question. Essayez l'index."
        )
