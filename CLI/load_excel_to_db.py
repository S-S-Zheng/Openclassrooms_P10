"""
Module ETL : Extraction, Transformation et Chargement des données NBA.
Respecte les principes de responsabilité unique (SRP) et de modularité.
"""

import pandas as pd
import logging
from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from livrable_p10.app.db.base import Base
from livrable_p10.app.db.models_db import Team, Player, Stat, Report
from livrable_p10.app.utils.config import DATABASE_URL, EXCEL_INPUT


logger = logging.getLogger(__name__)


# =====================================================================
# ======================== HELPERS POUR ORGANISATION DES TABLES ========================

# REPORT
def _ingest_reports(session: Session, df_dict: pd.DataFrame) -> None:
    """
    Gère la table Report.
    
    Args:
        session (Session): Session d'interaction avec la base
        df_dict (pd.DataFrame): Dataframe du dictionnaire de donnée
    """
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Report).delete()

    for _, row in df_dict.iterrows():
        session.add(Report(user_query=str(row.iloc[0]), ai_response=str(row.iloc[1])))

# TEAM
def _ingest_teams(session: Session, df_stats: pd.DataFrame, df_teams: pd.DataFrame) -> None:
    """Calcule les agrégations et remplit la table Team."""
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Team).delete()

    # Agrégation logique métier
    team_stats = df_stats.groupby('Team').agg({
        'Player': 'count',
        'PTS': 'sum',
        'GP': 'sum',
        'W': 'sum', 
        'L': 'sum',
        'PF': 'sum',
        'PIE': 'mean',
        'PACE': 'mean',
        'POSS': 'mean'
    }).reset_index()

    for _, row in team_stats.iterrows():
        full_name_match = df_teams[df_teams['Abbreviation'] == row['Team']]['Full_Name'].values
        full_name = full_name_match[0] if len(full_name_match) > 0 else row['Team']

        session.add(Team(
            abbreviation=row['Team'],
            full_name=full_name,
            player_count=int(row['Player']),
            total_points=int(row['PTS']),
            total_gp=int(row['GP']),
            total_wins=int(row['W']),
            total_losses=int(row['L']),
            total_fault=int(row['PF']),
            mean_pie=float(row['PIE']),
            mean_pace=float(row['PACE']),
            mean_poss=float(row['POSS'])
        ))

# PLAYER AND STATS
def _ingest_players_and_stats(session: Session, df_stats: pd.DataFrame) -> None:
    """Normalise les données joueurs et leurs statistiques associées."""
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Stat).delete()
    session.query(Player).delete()

    for _, row in df_stats.iterrows():
        player = Player(name=row['Player'])
        session.add(player)
        session.flush()  # Nécessaire pour obtenir l'ID avant l'insertion de Stat

        session.add(Stat(
            player_id=player.id,
            team_abbr=row['Team'],
            points=row['PTS'],
            gp=row['GP'],
            win=row['W'],
            lose=row['L']
            # Note : Déployer les 40+ colonnes ici ou via un dictionnaire **kwargs
        ))


# ======================== CHARGEMENT DE LA DONNÉE ========================

def load_excel_data(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Charge les feuilles Excel.

    Args:
        file_path (str): chemin du fichier excel à charger

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            * df_stats: df de la feuille ``Données NBA``
            * df_dict: df de la feuille ``Dictionnaire des données``
            * df_teams: df de la feuille ``Equipe``
    """
    logger.info(f"Chargement des données depuis {file_path}")
    # header des feuilles Données NBA et Dictionnaire des données comment à la ligne 2 tandis
    # que pour Equipe, c'est la ligne 1.
    df_stats = pd.read_excel(file_path, sheet_name="Données NBA", header=1)
    df_dict = pd.read_excel(file_path, sheet_name="Dictionnaire des données", header=1)
    df_teams = pd.read_excel(file_path, sheet_name="Equipe", header=0)
    return df_stats, df_dict, df_teams


# =================================== MAIN ===============================


def run_etl() -> None:
    """Orchestre le pipeline ETL complet."""
    engine = create_engine(DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    
    with session_factory() as session:
        try:
            # 1. Extraction
            df_stats, df_dict, df_teams = load_excel_data(EXCEL_INPUT)

            # 2. Transformation & Chargement
            logger.info("Début de l'ingestion des tables...")
            _ingest_reports(session, df_dict)
            _ingest_teams(session, df_stats, df_teams)
            _ingest_players_and_stats(session, df_stats)

            session.commit()
            logger.info("Pipeline ETL exécuté avec succès.")
        except Exception as e:
            session.rollback()
            logger.error(f"Échec critique de l'ETL : {e}")
            raise


# ==============================================================


if __name__ == "__main__":
    run_etl()