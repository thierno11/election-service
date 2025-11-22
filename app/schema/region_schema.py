"""Schémas Pydantic pour les régions."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schema.departement_schema import DepartementReponse1
from typing import List

class RegionSchema(BaseModel):
    """
    Schéma pour la création et modification d'une région.

    Attributes:
        nom_region: Nom de la région (minimum 2 caractères, maximum 100)
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    nom_region: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nom de la région",
        examples=["Dakar", "Thiès", "Saint-Louis"]
    )

    @field_validator("nom_region")
    @classmethod
    def validate_and_transform_region(cls, value: str) -> str:
        """
        Valide et transforme le nom de la région.

        Args:
            value: Le nom de la région
 
        Returns:
            str: Le nom en majuscules et nettoyé

        Raises:
            ValueError: Si le nom contient des caractères invalides
        """
        if not value or not value.strip():
            raise ValueError("Le nom de la région ne peut pas être vide")

        # Nettoyer et normaliser
        cleaned_value = value.strip()

        # Vérifier les caractères autorisés (lettres, espaces, tirets, apostrophes)
        import re
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", cleaned_value):
            raise ValueError(
                "Le nom de la région ne peut contenir que des lettres, espaces, tirets et apostrophes"
            )

        # Éviter les répétitions d'espaces
        cleaned_value = re.sub(r'\s+', ' ', cleaned_value)

        return cleaned_value.upper()


class RegionReponse(BaseModel):
    """
    Schéma de réponse pour une région avec ses statistiques.

    Attributes:
        id_region: Identifiant unique de la région
        nom_region: Nom de la région
        nombre_departement: Nombre de départements dans cette région
    """
    model_config = ConfigDict(from_attributes=True)

    id_region: int = Field(
        ...,
        description="Identifiant unique de la région",
        examples=[1, 2, 3]
    )

    nom_region: str = Field(
        ...,
        description="Nom de la région",
        examples=["DAKAR", "THIÈS", "SAINT-LOUIS"]
    )

    nombre_departement: int = Field(
        ...,
        ge=0,
        description="Nombre de départements dans cette région",
        examples=[0, 3, 5]
    )
    departements: Optional[List[DepartementReponse1]] = Field(
        None,
        description="Liste des départements dans cette région (optionnel)",
        examples=[[]]
    )


class RegionDetailReponse(RegionReponse):
    """
    Schéma de réponse détaillée pour une région avec informations supplémentaires.

    Attributes:
        departements: Liste des noms des départements (optionnel)
    """
    departements: Optional[list[str]] = Field(
        None,
        description="Liste des noms des départements dans cette région",
        examples=[["DAKAR", "PIKINE", "GUÉDIAWAYE"]]
    )