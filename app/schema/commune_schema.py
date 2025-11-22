from pydantic import BaseModel,field_validator
from typing import Optional, List
from app.schema.centre_votes_schema import CentreVoteReponse1


class CommuneSchema(BaseModel):
    nom_commune : str
    id_departement : int

    @field_validator("nom_commune")
    def transform_region(cls,value:str):
        return value.capitalize()
    
    class Config:
        from_attributes=True

class CommuneReponse(CommuneSchema):
    id_commune: int
    nombre_centre_vote: int
    centres_vote: Optional[List[CentreVoteReponse1]] = None

class CommuneReponse1(BaseModel):
    """Schéma simple pour les communes dans les réponses imbriquées."""
    id_commune: int
    nom_commune: str
    id_departement: int

    class Config:
        from_attributes = True
