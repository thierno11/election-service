from typing import TYPE_CHECKING, List
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.connexion import Base
from app.schema.departement_schema import DepartementReponse1
from datetime import datetime

if TYPE_CHECKING:
    from app.model.departement_model import Departement


class Region(Base):
    """
    Modèle représentant une région administrative.

    Attributes:
        id_region: Identifiant unique de la région
        nom_region: Nom de la région (unique)
        is_deleted: Indique si la région est supprimée (soft delete)
        created_at: Date de création
        updated_at: Date de dernière mise à jour
        departements: Liste des départements dans cette région
    """

    __tablename__ = "Regions"

    id_region: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique de la région"
    )

    nom_region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Nom de la région"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si la région est supprimée (soft delete)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date de création de l'enregistrement"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Date de dernière mise à jour de l'enregistrement"
    )

    # Relation avec les départements
    departements: Mapped[List["DepartementReponse1"]] = relationship(
        "Departement",
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self) -> str:
        """Représentation string de la région."""
        return f"<Region(id={self.id_region}, nom='{self.nom_region}', deleted={self.is_deleted})>"

    def __str__(self) -> str:
        """Représentation string lisible de la région."""
        return self.nom_region
