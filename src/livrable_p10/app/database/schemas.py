

# imports
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class PlayerStat(BaseModel):
    player_name: str
    match_date: datetime
    points: int = Field(ge=0)
    three_p_made: int = Field(ge=0)
    three_p_attempted: int = Field(ge=0)
    rebounds: int = Field(ge=0)
    is_home: bool

    @field_validator('three_p_made')
    def check_consistency(cls, value, values):
        if 'three_p_attempted' in values and value > values['three_p_attempted']:
            raise ValueError("Réussite supérieure aux tentatives !")
        return value