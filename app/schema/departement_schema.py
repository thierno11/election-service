"""Schémas Pydantic pour les départements."""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schema.commune_schema import CommuneReponse1
import re


class DepartementSchema(BaseModel):
    """
    Schéma pour la création et modification d'un département.

    Attributes:
        nom_departement: Nom du département (minimum 2 caractères, maximum 100)
        id_region: Identifiant de la région parente[]]
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    nom_departement: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nom du département",
        examples=["Dakar", "Thiès", "Louga"]
    )

    id_region: int = Field(
        ...,
        gt=0,
        description="Identifiant de la région parente",
        examples=[1, 2, 3]
    )

    @field_validator("nom_departement")
    @classmethod
    def validate_and_transform_departement(cls, value: str) -> str:
        """
        Valide et transforme le nom du département.

        Args:
            value: Le nom du département

        Returns:
            str: Le nom nettoyé et formaté

        Raises:
            ValueError: Si le nom contient des caractères invalides
        """
        if not value or not value.strip():
            raise ValueError("Le nom du département ne peut pas être vide")

        # Nettoyer et normaliser
        cleaned_value = value.strip()

        # Vérifier les caractères autorisés
        # import re

        cleaned_value = value.strip()
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-']+$", cleaned_value):
            raise ValueError(
            "Le nom du département ne peut contenir que des lettres, chiffres, espaces, tirets et apostrophes"
        )

        # Éviter les répétitions d'espaces
        cleaned_value = re.sub(r'\s+', ' ', cleaned_value)

        # Capitaliser chaque mot
        return cleaned_value.title()


class DepartementReponse(BaseModel):
    """
    Schéma de réponse pour un département avec ses statistiques.

    Attributes:
        id_departement: Identifiant unique du département
        nom_departement: Nom du département
        id_region: Identifiant de la région parente
        nombre_commune: Nombre de communes dans ce département
    """
    model_config = ConfigDict(from_attributes=True)

    id_departement: int = Field(
        ...,
        description="Identifiant unique du département",
        examples=[1, 2, 3]
    )

    nom_departement: str = Field(
        ...,
        description="Nom du département",
        examples=["Dakar", "Thiès", "Louga"]
    )

    id_region: int = Field(
        ...,
        description="Identifiant de la région parente",
        examples=[1, 2, 3]
    )

    nombre_commune: int = Field(
        ...,
        ge=0,
        description="Nombre de communes dans ce département",
        examples=[0, 5, 10]
    )

    communes: Optional[List[CommuneReponse1]] = Field(
        None,
        description="Liste des communes dans ce département (optionnel)",
        examples=[[]]
    )


class DepartementDetailReponse(DepartementReponse):
    """
    Schéma de réponse détaillée pour un département.

    Attributes:
        nom_region: Nom de la région parente
        communes: Liste des noms des communes (optionnel)
    """
    nom_region: Optional[str] = Field(
        None,
        description="Nom de la région parente",
        examples=["DAKAR", "THIÈS"]
    )

    communes: Optional[list[str]] = Field(
        None,
        description="Liste des noms des communes dans ce département",
        examples=[["Dakar", "Pikine", "Guédiawaye"]]
    )

class DepartementReponse1(BaseModel):
    """
    Schéma de réponse pour un département avec ses statistiques.

    Attributes:
        id_departement: Identifiant unique du département
        nom_departement: Nom du département
        id_region: Identifiant de la région parente
        nombre_commune: Nombre de communes dans ce département
    """
    model_config = ConfigDict(from_attributes=True)

    id_departement: int = Field(
        ...,
        description="Identifiant unique du département",
        examples=[1, 2, 3]
    )

    nom_departement: str = Field(
        ...,
        description="Nom du département",
        examples=["Dakar", "Thiès", "Louga"]
    )

    id_region: int = Field(
        ...,
        description="Identifiant de la région parente",
        examples=[1, 2, 3]
    )
