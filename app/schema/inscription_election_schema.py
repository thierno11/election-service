"""Schémas Pydantic pour les inscriptions d'élection."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InscriptionElectionSchema(BaseModel):
    """
    Schéma pour créer une inscription d'élection.
    """
    id_election: int = Field(..., description="Identifiant de l'élection")
    nom_candidat: str = Field(..., description="Nom du candidat")
    date_election: date = Field(..., description="Date de l'élection")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_election": 1,
                "nom_candidat": "Jean Dupont",
                "date_election": "2024-02-25"
            }
        }


class InscriptionElectionReponse(BaseModel):
    """
    Schéma de réponse pour une inscription d'élection.
    """
    id_election: int = Field(..., description="ID de l'élection")
    id_candidat: int = Field(..., description="ID du candidat")
    date_election: date = Field(..., description="Date de l'élection")
    created_at: datetime = Field(..., description="Date et heure de création")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_election": 1,
                "id_candidat": 5,
                "date_election": "2024-02-25",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class InscriptionElectionAvecDetails(BaseModel):
    """
    Schéma de réponse pour une inscription avec détails du candidat et de l'élection.
    """
    id_election: int = Field(..., description="ID de l'élection")
    id_candidat: int = Field(..., description="ID du candidat")
    date_election: date = Field(..., description="Date de l'élection")
    created_at: datetime = Field(..., description="Date et heure de création")
    nom_candidat: Optional[str] = Field(None, description="Nom du candidat")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_election": 1,
                "id_candidat": 5,
                "date_election": "2024-02-25",
                "created_at": "2024-01-15T10:30:00Z",
                "nom_candidat": "Jean Dupont"
            }
        }


class InscriptionElectionItem(BaseModel):
    """
    Schéma pour un élément d'inscription dans une opération en masse.
    """
    id_candidat: int = Field(..., description="identifiant candidat")

    class Config:
        from_attributes = True


class InscriptionElectionBulkSchema(BaseModel):
    """
    Schéma pour créer plusieurs inscriptions d'élection en masse.
    """
    id_election: int = Field(..., description="Identifiant de l'élection")
    date_election: date = Field(..., description="Date de l'élection")
    candidats: List[InscriptionElectionItem] = Field(..., description="Liste des candidats à inscrire")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_election": 1,
                "date_election": "2024-02-25",
                "candidats": [
                    {"id_candidat": 1},
                    {"id_candidat": 2},
                    {"id_candidat": 3}
                ]
            }
        }