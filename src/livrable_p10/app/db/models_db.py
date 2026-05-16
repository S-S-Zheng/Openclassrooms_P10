"""
Module de définition des modèles de données ORM (Object-Relational Mapping).

Ce module contient les schémas SQL pour la base via SQLAlchemy. Il définit
l'organisation des données stockées, incluant les enregistrements de prédictions
détaillés et le système de journalisation (logging) pour la traçabilité des requêtes.
"""

# Pydantic définit la forme des données qui entrent/sortent,
# SQLAlchemy définit la forme des données qui dorment en base.

# imports
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

# from sqlalchemy.dialects.postgresql import JSONB # Pour Supabase plus tard si besoin
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from livrable_p10.app.db.base import Base


# ================= DONNÉES MÉTIER (RAG / SQL Tool) =================
class Player(Base):
    """
    Table d'identité des joueurs.\n
    Représente l'entité de base pour l'identification. Chaque joueur est lié
    à une ou plusieurs lignes de statistiques via une relation 1:N.

    Attributes:
        id (int): Clé primaire auto-incrémentée.
        name (str): Nom du joueur
    """

    __tablename__ = "players"

    # Identifications
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False)

    # Relations
    # Crée une dépendance des ID avec la table stats (permet la jointure)
    # Créée une relation bidirectionnelle entre stats et players
    stats = relationship("Stat", back_populates="player", cascade="all, delete-orphan")


class Stat(Base):
    """
    Table des statistiques détaillées par joueur.\n
    """

    __tablename__ = "stats"

    # Identifications
    id = Column(Integer, primary_key=True)
    team_abbr = Column(String(3), ForeignKey("teams.abbreviation"), index=True)

    age = Column(Integer)
    gp = Column(Integer)
    win = Column(Integer)
    lose = Column(Integer)
    time_played = Column(Float)
    points = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    fg_pct = Column(Float)
    fifteen = Column(Integer)
    three_p_tried = Column(Integer)
    three_p_pct = Column(Float)
    ftm = Column(Integer)
    fta = Column(Integer)
    ft_pct = Column(Float)
    oreb = Column(Integer)
    dreb = Column(Integer)
    reb = Column(Integer)
    assists = Column(Integer)
    turnovers = Column(Integer)
    steal = Column(Integer)
    blocks = Column(Integer)
    faults = Column(Integer)
    fantasy_points = Column(Integer)
    doubles = Column(Integer)
    triples = Column(Integer)
    plus_minus = Column(Float)
    off_rate = Column(Float)
    def_rate = Column(Float)
    net_rate = Column(Float)
    assists_pct = Column(Float)
    assists_turnovers_rate = Column(Float)
    assists_rate = Column(Float)
    oreb_pct = Column(Float)
    dreb_pct = Column(Float)
    reb_pct = Column(Float)
    turnovers_rate = Column(Float)
    efg_pct = Column(Float)
    ts_pct = Column(Float)
    usg_pct = Column(Float)
    pace = Column(Float)
    pie = Column(Float)
    poss = Column(Integer)

    # Relations
    # Crée une dépendance des ID avec la table players (permet la jointure)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    # Créée une relation bidirectionnelle entre stats et players
    player = relationship("Player", back_populates="stats")


class Team(Base):
    """
    Table renseignant les caractéristiques des équipes. Lie le code à 3 lettres avec le nom
    complet de l'équipe et agrège quelques features.
    """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String(3), unique=True, index=True, nullable=False)
    full_name = Column(String(50), nullable=False)

    player_count = Column(Integer)
    total_points = Column(Integer)
    total_gp = Column(Integer)
    total_wins = Column(Integer)
    total_losses = Column(Integer)
    total_fault = Column(Integer)
    mean_pie = Column(Float)
    mean_pace = Column(Float)
    mean_poss = Column(Float)
    mean_ts = Column(Float)


# ================= MONITORING =================


class Report(Base):
    """
    Modèle représentant les logs d'activité.\n
    Stocke les métadonnées de chaque requête entrante.

    Attributes:
        id (int): Clé primaire auto-incrémentée.
        created_at (datetime): Horodatage de la requête (géré par le serveur SQL).
        status_code (int): Le code de statut HTTP retourné (ex: 200, 422, 500).
        response_time_ms (float): Temps de traitement de la requête en millisecondes.
        user_query (str): La question utilisateur.
    """

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_query = Column(Text)
    sql_generated = Column(Text)

    status_code = Column(Text)
    response_time_ms = Column(Float)
