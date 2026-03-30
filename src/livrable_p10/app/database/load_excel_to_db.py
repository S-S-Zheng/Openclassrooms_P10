


# Imports
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
import logging

from livrable_p10.app.database.schemas import PlayerStat
from livrable_p10.app.tools.rag.utils.config import DATABASE_URL, EXCEL_INPUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# --- Modèles SQLAlchemy ---
class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class MatchStat(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    date = Column(DateTime, nullable=False)
    points = Column(Integer)
    three_p_made = Column(Integer)
    three_p_attempted = Column(Integer)
    rebounds = Column(Integer)
    is_home = Column(Boolean)

def run_ingestion(excel_path: str):
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    logger.info(f"Lecture de l'Excel: {excel_path}")
    df = pd.read_excel(excel_path)

    # Dictionnaire pour mettre en cache les IDs des joueurs et éviter les doublons
    player_cache = {}

    for index, row in df.iterrows():
        try:
            # Validation Pydantic (fail-fast)
            stat_data = PlayerStat(
                player_name=row['Player'],
                match_date=pd.to_datetime(row['Date']),
                points=int(row['PTS']),
                three_p_made=int(row['3P_Made']),
                three_p_attempted=int(row['3P_Att']),
                rebounds=int(row['TRB']),
                is_home=bool(row['Home_Away'] == 'Home')
            )

            # Gestion du Joueur (Relationnel)
            if stat_data.player_name not in player_cache:
                player = session.query(Player).filter_by(name=stat_data.player_name).first()
                if not player:
                    player = Player(name=stat_data.player_name)
                    session.add(player)
                    session.flush() # Pour récupérer l'ID
                player_cache[stat_data.player_name] = player.id

            # Insertion de la Stat
            new_stat = MatchStat(
                player_id=player_cache[stat_data.player_name],
                date=stat_data.match_date,
                points=stat_data.points,
                three_p_made=stat_data.three_p_made,
                three_p_attempted=stat_data.three_p_attempted,
                rebounds=stat_data.rebounds,
                is_home=stat_data.is_home
            )
            session.add(new_stat)

        except Exception as e:
            logger.error(f"Erreur ligne {index} : {e}")
            continue

    session.commit()
    logger.info("Ingestion terminée avec succès.")


# ================================================================


if __name__ == "__main__":
    run_ingestion(EXCEL_INPUT)