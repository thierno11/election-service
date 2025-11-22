"""Schémas Pydantic pour les candidats."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidatSchema(BaseModel):
    """
    Schéma pour la création et modification d'un candidat.

    Attributes:
        nom_candidat: Nom du candidat
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    nom_candidat: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nom du candidat",
        examples=["MACKY SALL", "OUSMANE SONKO"]
    )

    @field_validator("nom_candidat")
    @classmethod
    def to_upper(cls, value: str) -> str:
        """Convertit le nom du candidat en majuscules."""
        if value:
            return value.upper()
        return value


class CandidatReponse(BaseModel):
    """
    Schéma de réponse pour un candidat.

    Attributes:
        id_candidat: Identifiant unique du candidat
        nom_candidat: Nom du candidat
    """
    model_config = ConfigDict(from_attributes=True)

    id_candidat: int = Field(
        ...,
        description="Identifiant unique du candidat",
        examples=[1, 2, 3]
    )

    nom_candidat: str = Field(
        ...,
        description="Nom du candidat",
        examples=["MACKY SALL", "OUSMANE SONKO"]
    )