from pydantic import BaseModel, field_validator
from typing import Optional, List, TYPE_CHECKING



class BureauVoteReponse(BaseModel):
    id_bureau: int
    numero_bureau: int
    implantation: str
    id_centre: int
    centre_vote: Optional["CentreVoteReponse1"] = None

    class Config:
        from_attributes = True

class CentreVotesSchema(BaseModel):
    """Schéma pour créer/modifier un centre de vote."""
    nom_centre: str
    id_commune: int

    @field_validator("nom_centre")
    def transform_nom_centre(cls, value: str):
        return value.upper()

    class Config:
        from_attributes = True


class CentreVotesReponse(BaseModel):
    """Schéma de réponse pour un centre de vote."""
    id_centre: int
    nom_centre: str
    id_commune: int
    nombre_bureaux: int = 0
    bureaux_vote: Optional[List["BureauVoteReponse"]] = None

    class Config:
        from_attributes = True


class CentreVoteReponse1(BaseModel):
    """Schéma simple pour les centres dans les réponses imbriquées."""
    id_centre: int
    nom_centre: str
    id_commune: int

    class Config:
        from_attributes = True


# # Résolution des références forward après toutes les définitions
# def _resolve_forward_refs():
#     from schema.bureau_vote_schema import BureauVoteReponse
#     CentreVotesReponse.model_rebuild()

# # Appel différé pour éviter les imports circulaires
# try:
#     _resolve_forward_refs()
# except ImportError:
#     pass
