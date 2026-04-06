"""
Chargement des données tabulaires dans la base de donnée.

Workflow
----
* SQLAlchemy supprime les tables existantes (si elles existent).
* SQLAlchemy crée les tables players, stats, teams et reports toutes neuves.
* Pandas lit l'Excel.
* Pydantic valide chaque ligne.
* SQLAlchemy insère les données proprement.
"""

import pandas as pd
import logging
from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from livrable_p10.app.db.base import Base
from livrable_p10.app.db.models_db import Team, Player, Stat, Report
from livrable_p10.app.utils.config import DATABASE_URL, EXCEL_INPUT
from livrable_p10.app.utils.schemas import NBAInputSchema, TeamInputSchema
from livrable_p10.app.db.create_db import init_db

logger = logging.getLogger(__name__)


# =====================================================================
# ======================== HELPERS POUR ORGANISATION DES TABLES ========================

# REPORT
def _clean_reports(session: Session) -> None:
    """
    Nettoye la table Report.

    Args:
        session (Session): Session d'interaction avec la base
    """
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Report).delete()

# PLAYER AND STATS
def _ingest_players_and_stats(session: Session, df_stats: pd.DataFrame) -> None:
    """Normalise les données joueurs et leurs statistiques associées."""
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Stat).delete()
    session.query(Player).delete()
    session.flush()

    # Dictionnaire éviter les doublons durant la saison (ex: transfert)
    player_cache = {}

    for _, row in df_stats.iterrows():
        # Nettoyage des NaN : on transforme les NaN en None
        row_dict = row.where(pd.notnull(row), None).to_dict()

        # On a déjà tout renseigné dans le pydantic, on va donc l'utiliser pour le mapping
        # (Validation + Mapping des alias)
        # ``model_validate`` utilise les alias pour remplir les champs
        try:
            validated_data = NBAInputSchema.model_validate(row_dict)
        except Exception as e:
            logger.error(f"Erreur de validation pour le joueur {row.get('Player')}: {e}")
            continue

        # # --------- Gestion du Joueur (idempotence) -----------
        player_name = validated_data.player_name
        if player_name not in player_cache:
            p = Player(name=player_name)
            session.add(p)
            session.flush()
            player_cache[player_name] = p.id

        #  -------------- Gestion des Stats ---------------
        # .model_dump() transforme l'objet Pydantic en dict { "points": 25, ... }
        # On exclut le nom du joueur et le code a 3 lettres
        stat_fields = validated_data.model_dump(exclude={'player_name', 'team_abbr'})

        stat_entry = Stat(
            player_id=player_cache[player_name],
            team_abbr=validated_data.team_abbr,
            **stat_fields
        )
        session.add(stat_entry)

# TEAM
def _ingest_teams(
    session: Session,
    df_stats: pd.DataFrame,
    df_teams: pd.DataFrame
) -> None:
    """Calcule les agrégations et remplit la table Team."""
    # Evite l'idempotence en effaçant le contenu de la table
    session.query(Team).delete()

    # for _, row in df_teams.iterrows():
    #     # On transforme la ligne Excel en dictionnaire
    #     row_dict = row.to_dict()

    #     # On a déjà tout renseigné dans le pydantic, on va donc l'utiliser pour le mapping
    #     # (Validation + Mapping des alias)
    #     # ``model_validate`` utilise les alias pour remplir les champs
    #     try:
    #         validated_data = TeamInputSchema.model_validate(row_dict)
    #         team_fields = validated_data.model_dump()
    #     except Exception as e:
    #         logger.error(f"Erreur format équipe : {row.get('Code')} - {e}")
    #         continue
    # 1. Validation de TOUTES les équipes et stockage dans une liste
    validated_teams_data = []
    for _, row in df_teams.iterrows():
        try:
            validated_data = TeamInputSchema.model_validate(row.to_dict())
            # On récupère le dict avec les noms de champs Pydantic (ex: team_abbr)
            validated_teams_data.append(validated_data.model_dump())
        except Exception as e:
            logger.error(f"Erreur format équipe : {row.get('Code')} - {e}")
            continue
    df_teams_checked = pd.DataFrame(validated_teams_data)

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
        'POSS': 'mean',
        'TS%': 'mean'
    }).reset_index()

    for _, row in team_stats.iterrows():
        team_abbr = str(row['Team'])
        # match = df_teams[df_teams['Code'] == team_abbr]
        match = df_teams_checked[df_teams_checked['team_abbr'] == team_abbr]
        if not match.empty:
            # full_name = str(match["Nom complet de l'équipe"].iloc[0])
            full_name = str(match["full_name"].iloc[0])
        else:
            logger.warning(f"Erreur de team code, {team_abbr} n'a pas de correspondance...")
            full_name = "Unknown"

        session.add(Team(
            abbreviation=team_abbr,
            full_name=full_name,
            player_count=int(row['Player']),
            total_points=int(row['PTS']),
            total_gp=int(row['GP']),
            total_wins=int(row['W']),
            total_losses=int(row['L']),
            total_fault=int(row['PF']),
            mean_pie=float(row['PIE']),
            mean_pace=float(row['PACE']),
            mean_poss=float(row['POSS']),
            mean_ts=float(row['TS%'])
        ))


# ======================== CHARGEMENT DE LA DONNÉE ========================

def load_excel_data(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge les feuilles Excel.

    Args:
        file_path (str): chemin du fichier excel à charger

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            * df_stats: df de la feuille ``Données NBA``
            * df_teams: df de la feuille ``Equipe``
    """
    logger.info(f"Chargement des données depuis {file_path}")

    # ------------------------ FILTRE ET NETTOYAGE ------------------------
    # header feuille Données NBA commence à la ligne 2 tandis
    # que pour Equipe et Dictionnaire des données, col'est la ligne 1.
    df_stats = pd.read_excel(file_path, sheet_name="Données NBA", header=1)
    # df_dict = pd.read_excel(file_path, sheet_name="Dictionnaire des données", header=0)
    df_teams = pd.read_excel(file_path, sheet_name="Equipe", header=0)

    # # Force tous les noms de colonnes en string et strip les espaces
    # df_stats.columns = [str(col).strip() for col in df_stats.columns]

    # # Filtre des colonnes "fantômes"
    # # On ne garde que les colonnes qui ne commencent pas par "Unnamed"
    # df_stats = df_stats.loc[:, ~df_stats.columns.str.contains('^Unnamed', na=False)]
    # df_teams = df_teams.loc[:, ~df_teams.columns.str.contains('^Unnamed', na=False)]

    # # Application .strip() sur les string
    # # Sur les headers
    # for df in [df_stats, df_teams]:
    #     df.columns = df.columns.str.strip()
    # # Sur les colonnes concernées
    # df_stats['Player'] = df_stats['Player'].astype(str).str.strip()
    # df_stats['Team'] = df_stats['Team'].astype(str).str.strip()
    # df_teams['Code'] = df_teams['Code'].astype(str).str.strip()
    # df_teams["Nom complet de l'équipe"] = \
    #     df_teams["Nom complet de l'équipe"].astype(str).str.strip()
    # # df_dict['Dictionnaire des données'] = \
    # #     df_dict['Dictionnaire des données'].astype(str).str.strip()

    # Headers
    for df in [df_stats, df_teams]:
        # headers = str + strip()
        df.columns = [str(col).strip() for col in df.columns]
        # Drop les colonnes vides
        df.drop(
            columns=[col for col in df.columns if "Unnamed" in col or col == "nan"],
            inplace=True
        )

    # nettoyage des espacements
    df_stats['Player'] = df_stats['Player'].astype(str).str.strip()
    df_stats['Team'] = df_stats['Team'].astype(str).str.strip()
    df_teams['Code'] = df_teams['Code'].astype(str).str.strip()
    df_teams["Nom complet de l'équipe"] = \
        df_teams["Nom complet de l'équipe"].astype(str).str.strip()

    return df_stats, df_teams


# =================================== MAIN ===============================


def run_etl() -> None:
    """Orchestre le pipeline ETL complet."""
    engine = create_engine(DATABASE_URL)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        try:
            # Extraction et nettoyage des headers
            df_stats, df_teams = load_excel_data(EXCEL_INPUT)
            # Nettoyage de la table Report
            _clean_reports(session)

            logger.info("Début de l'ingestion des tables...")
            # Ingestion Player et Stat (NBAInputSchema)
            _ingest_players_and_stats(session, df_stats)
            # Ingestion Teams (TeamInputSchema)
            _ingest_teams(session, df_stats, df_teams)

            session.commit()
            logger.info("Pipeline ETL exécuté avec succès.")
        except Exception as e:
            session.rollback()
            logger.error(f"Échec critique de l'ETL : {e}")
            raise


# ==============================================================


if __name__ == "__main__":
    try:
        logger.info("ETL des données tabulaires dans la DB")
        # On drop toutes les tables et on ré-init
        # ==> on pourrait enlever les lignes de delete dans chaque fonction d'ingestion mais
        # juste pour être sûr, on les laisse pour le moment.
        init_db(reset_tables=True)

        # On lance l'ETL
        run_etl()

        logger.info("DB chargé")
    except Exception as e:
        logger.critical(f"Erreur de chargement de la DB : {e}")