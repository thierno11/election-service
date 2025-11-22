from pydantic import BaseModel, Field, field_validator,ConfigDict


class ElectionSchema(BaseModel):
    """
    Schéma pour la création et modification d'une élection.

    Attributes:
        type_election: Type d'élection
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    type_election: str = Field(
        ...,
        description="Type d'élection",
        examples=["presidentielle", "legislative", "locale"]
    )

    @field_validator("type_election")
    @classmethod
    def validate_type_election(cls, value: str) -> str:
        """
        Convertit le type d'élection en majuscules.

        Args:
            value: Le type d'élection

        Returns:
            str: Le type d'élection en majuscules
        """
        if value:
            return value.upper()
        return value


class ElectionReponse(BaseModel):
    """
    Schéma de réponse pour une élection.

    Attributes:
        id_election: Identifiant unique de l'élection
        type_election: Type d'élection
    """
    model_config = ConfigDict(from_attributes=True)

    id_election: int = Field(
        ...,
        description="Identifiant unique de l'élection",
        examples=[1, 2, 3]
    )

    type_election: str = Field(
        ...,
        description="Type d'élection",
        examples=["presidentielle", "legislative"]
    )
