from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING

from app.schema.centre_votes_schema import CentreVoteReponse1


# Schema pour créer ou recevoir un bureau de vote
class BureauVoteSchema(BaseModel):
    numero_bureau: int
    implantation: str
    id_centre: int

    class Config:
        from_attributes = True


class BureauVoteReponse(BaseModel):
    id_bureau: int
    numero_bureau: int
    implantation: str
    id_centre: int
    centre_vote: Optional["CentreVoteReponse1"] = None

    class Config:
        from_attributes = True


# # Résolution des références forward après toutes les définitions
# def _resolve_forward_refs():
#     from schema.centre_votes_schema import CentreVoteReponse1
#     BureauVoteReponse.model_rebuild()

# # Appel différé pour éviter les imports circulaires
# try:
#     _resolve_forward_refs()
# except ImportError:
#     pass
