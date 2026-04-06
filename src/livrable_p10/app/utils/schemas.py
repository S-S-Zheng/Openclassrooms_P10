"""
Module de définition des schémas Pydantic pour la base de donnée.

|Abreviation|Définition|
|-----------|----------|
|Player|Nom du joueur|
|Team|Équipe du joueur (code à 3 lettres)|
|Age|Âge du joueur|
|GP|Nombre de matchs joués (Games Played)|
|W|Nombre de victoires de l'équipe lors des matchs joués|
|L|Nombre de défaites|
|Min|Minutes moyennes jouées par match|
|PTS|Points marqués en moyenne par match|
|FGM|Tirs réussis par match (Field Goals Made)|
|FGA|Tirs tentés par match (Field Goals Attempted)|
|FG%|Pourcentage de réussite aux tirs|
|15:00:00|Minutes jouées après 15:00 de jeu|
|3PA|Tirs à 3 points tentés par match|
|3P%|Pourcentage de réussite à 3 points|
|FTM|Lancers francs réussis (Free Throws Made)|
|FTA|Lancers francs tentés|
|FT%|Pourcentage de réussite aux lancers francs|
|OREB|Rebonds offensifs|
|DREB|Rebonds défensifs|
|REB|Rebonds totaux|
|AST|Passes décisives (Assists)|
|TOV|Balles perdues (Turnovers)|
|STL|Interceptions (Steals)|
|BLK|Contres (Blocks)|
|PF|Fautes personnelles|
|FP|Fantasy Points|
|DD2|Double-doubles (≥10 dans deux catégories principales)|
|TD3|Triple-doubles (≥10 dans trois catégories principales)|
|+ / -|Plus-Minus (écart de score lorsque le joueur est sur le terrain)|
|OFFRTG|Offensive Rating (points marqués par 100 possessions)|
|DEFRTG|Defensive Rating (points encaissés par 100 possessions)|
|NETRTG|Net Rating = OFFRTG - DEFRTG|
|AST%|Pourcentage d'assists – implication dans les passes décisives|
|AST/TO|Ratio passes / pertes de balle|
|AST RATIO|Ratio d’assists pour 100 possessions|
|OREB%|Pourcentage de rebonds offensifs parmi ceux disponibles|
|DREB%|Idem en défensif|
|REB%|Pourcentage de rebonds totaux parmi ceux disponibles|
|TO RATIO|Turnover Ratio – pertes de balle par 100 possessions|
|EFG%|Effective Field Goal % (pondère les 3 points)|
|TS%|True Shooting % (inclut FG et FT dans l'efficacité)|
|USG%|Usage Rate – % des actions utilisées par le joueur|
|PACE|Rythme de jeu (possessions par 48 minutes)|
|PIE|Player Impact Estimate – évaluation globale de l’impact|
|POSS|Nombre total de possessions jouées|


"""
from pydantic import BaseModel, Field, field_validator


# ======================== STATS (et PLAYER) ========================

class NBAInputSchema(BaseModel):
    """Schéma de validation pour une ligne de la feuille NBA Données."""
    player_name: str = Field(
        ...,
        alias="Player",
        description="Nom du joueur"
    )
    team_abbr: str = Field(
        ...,
        alias="Team",
        description="Équipe du joueur (code à 3 lettres)"
    )
    age: int = Field(
        ...,
        alias="Age",
        ge=18,
        le=50,
        description="Âge du joueur"
    )
    gp:int = Field(
        ...,
        alias="GP",
        ge=0,
        le=100,
        description="Nombre de matchs joués (Games Played)"
    )
    win:int=Field(
        ...,
        alias="W",
        ge=0,
        le=100,
        description="Nombre de victoires de l'équipe lors des matchs joués"
    )
    lose:int=Field(
        ...,
        alias="L",
        ge=0,
        le=100,
        description="Nombre de défaites de l'équipe lors des matchs joués"
    )
    time_played:float=Field(
        ...,
        alias="Min",
        ge=0.0,
        le=60.0,
        description="Minutes moyennes jouées par match"
    )
    points: int = Field(
        ...,
        alias="PTS",
        ge=0,
        le=5000,
        description="Points marqués en moyenne par match"
    )
    fgm: int = Field(
        ...,
        alias="FGM",
        ge=0,
        le=2500,
        description="Tirs réussis par match (Field Goals Made)"
    )
    fga: int = Field(
        ...,
        alias="FGA",
        ge=0,
        le=2500,
        description="Tirs tentés par match (Field Goals Attempted)"
    )
    fg_pct: float = Field(
        ...,
        alias="FG%",
        ge=0.0,
        le=100.0,
        description="Pourcentage de réussite aux tirs"
    )
    fifteen:int=Field(
        ...,
        alias="15:00:00",
        ge=0,
        le=999,
        description="Minutes jouées après 15:00 de jeu"
    )
    three_p_tried:int=Field(
        ...,
        alias="3PA",
        ge=0,
        le=999,
        description="Tirs à 3 points tentés par match"
    )
    three_p_pct: float = Field(
        ...,
        alias="3P%",
        ge=0.0,
        le=100.0,
        description="Pourcentage de réussite à 3 points"
    )
    ftm: int = Field(
        ...,
        alias="FTM",
        ge=0,
        le=999,
        description="Lancers francs réussis (Free Throws Made)"
    )
    fta: int = Field(
        ...,
        alias="FTA",
        ge=0,
        le=999,
        description="Lancers francs tentés"
    )
    ft_pct: float = Field(
        alias="FT%",
        ge=0.0,
        le=100.0,
        description="Pourcentage de réussite aux lancers francs"
    )
    oreb: int = Field(
        alias="OREB",
        ge=0,
        le=999,
        description="Rebonds offensifs"
    )
    dreb: int = Field(
        alias="DREB",
        ge=0,
        le=999,
        description="Rebonds défensifs"
    )
    reb: int = Field(
        alias="REB",
        ge=0,
        le=2000,
        description="Rebonds totaux"
    )
    assists: int = Field(
        alias="AST",
        ge=0,
        le=999,
        description="Passes décisives (Assists)"
    )
    turnovers: int = Field(
        alias="TOV",
        ge=0,
        le=999,
        description="Balles perdues (Turnovers)"
    )
    steal: int = Field(
        alias="STL",
        ge=0,
        le=999,
        description="Interceptions (Steals)"
    )
    blocks: int = Field(
        alias="BLK",
        ge=0,
        le=999,
        description="Contres (Blocks)"
    )
    faults: int = Field(
        alias="PF",
        ge=0,
        le=999,
        description="Fautes personnelles"
    )
    fantasy_points: int = Field(
        alias="FP",
        ge=0,
        le=9999,
        description="Fantasy Points"
    )
    doubles: int = Field(
        alias="DD2",
        ge=0,
        le=99,
        description="Double-doubles (≥10 dans deux catégories principales)"
    )
    triples: int = Field(
        alias="TD3",
        ge=0,
        le=99,
        description="Triple-doubles (≥10 dans trois catégories principales)"
    )
    plus_minus: float = Field(
        alias="+/-",
        ge=-50.0,
        le=50.0,
        description="Plus-Minus (écart de score lorsque le joueur est sur le terrain)"
    )
    off_rate: float = Field(
        alias="OFFRTG",
        ge=0.0,
        le=999.0,
        description="Offensive Rating (points marqués par 100 possessions)"
    )
    def_rate: float = Field(
        alias="DEFRTG",
        ge=0.0,
        le=999.0,
        description="Defensive Rating (points encaissés par 100 possessions)"
    )
    net_rate: float = Field(
        alias="NETRTG",
        ge=-99.0,
        le=99.0,
        description="Net Rating = OFFRTG - DEFRTG"
    )
    assists_pct: float = Field(
        alias="AST%",
        ge=0.0,
        le=100.0,
        description="Pourcentage d'assists – implication dans les passes décisives"
    )
    assists_turnovers_rate: float = Field(
        alias="AST/TO",
        ge=0.0,
        le=99.0,
        description="Ratio passes / pertes de balle"
    )
    assists_rate: float = Field(
        alias="AST RATIO",
        ge=0.0,
        le=100.0,
        description="Ratio d’assists pour 100 possessions"
    )
    oreb_pct: float = Field(
        alias="OREB%",
        ge=0.0,
        le=100.0,
        description="Pourcentage de rebonds offensifs parmi ceux disponibles"
    )
    dreb_pct: float = Field(
        alias="DREB%",
        ge=-50.0,
        le=50.0,
        description="Pourcentage de rebonds défensif parmi ceux disponibles"
    )
    reb_pct: float = Field(
        alias="REB%",
        ge=0.0,
        le=100.0,
        description="Pourcentage de rebonds totaux parmi ceux disponibles"
    )
    turnovers_rate: float = Field(
        alias="TO RATIO",
        ge=0.0,
        le=100.0,
        description="Turnover Ratio – pertes de balle par 100 possessions"
    )
    efg_pct: float = Field(
        alias="EFG%",
        ge=0.0,
        le=125.0,
        description="Effective Field Goal % (pondère les 3 points)"
    )
    ts_pct: float = Field(
        alias="TS%",
        ge=0.0,
        le=125.0,
        description="True Shooting % (inclut FG et FT dans l'efficacité)"
    )
    usg_pct: float = Field(
        alias="USG%",
        ge=0.0,
        le=100.0,
        description="Usage Rate – pourcentage des actions utilisées par le joueur"
    )
    pace: float = Field(
        alias="PACE",
        ge=0.0,
        le=999.0,
        description="Rythme de jeu (possessions par 48 minutes))"
    )
    pie: float = Field(
        ...,
        alias="PIE",
        ge=-99.0,
        le=99.0,
        description="Player Impact Estimate – évaluation globale de l’impact"
    )
    poss: int = Field(
        ...,
        alias="POSS",
        ge=0,
        le=9999,
        description="Nombre total de possessions jouées"
    )


    @field_validator("efg_pct","ts_pct" )
    @classmethod
    def check_percentages(cls, value: float) -> float:
        """
        Vérifie les pourcentages.
        Remarque
        ----
        - Il faudra enlever les limiteurs type ge/le sinon Pydantic levera l'erreur avant fix
        - Ne concerne que efg_pct (EFG%) et ts_pct (TS%) pour le moment.
        """
        if not value <= 100:
            return value/10
        return value


# ======================== TEAM ========================


class TeamInputSchema(BaseModel):
    """Schéma de validation pour la feuille Equipe."""
    team_abbr: str = Field(
        ..., 
        alias="Code", 
        description="Équipe du joueur (code à 3 lettres)"
    )
    full_name: str = Field(
        ..., 
        alias="Nom complet de l'équipe",
        description="Nom complet de l'équipe"
    )