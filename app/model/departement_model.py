"""Modèle SQLAlchemy pour les départements."""

from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.connexion import Base

if TYPE_CHECKING:
    from app.model.region_model import Region
    from app.model.commune_model import Commune


class Departement(Base):
    """
    Modèle représentant un département administratif.

    Attributes:
        id_departement: Identifiant unique du département
        nom_departement: Nom du département (unique)
        id_region: Clé étrangère vers la région parente
        is_deleted: Indique si le département est supprimé (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour
        region: Région à laquelle appartient ce département
        communes: Liste des communes dans ce département
    """

    __tablename__ = "Departements"

    id_departement: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique du département"
    )

    nom_departement: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Nom du département"
    )

    id_region: Mapped[int] = mapped_column(
        ForeignKey("Regions.id_region", ondelete="CASCADE"),
        nullable=False,
        comment="Identifiant de la région parente"
    )

    # Indicateur de suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si le département est supprimé (soft delete)"
    )

    # Horodatage de création
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date de création de l'enregistrement"
    )

    # Horodatage de dernière mise à jour
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Date de dernière mise à jour de l'enregistrement"
    )

    # Relations
    region: Mapped["Region"] = relationship(
        "Region",
        back_populates="departements",
        lazy="select"
    )

    communes: Mapped[List["Commune"]] = relationship(
        "Commune",
        back_populates="departement",
        lazy="select"
    )

    def __repr__(self) -> str:
        """Représentation string du département."""
        return f"<Departement(id={self.id_departement}, nom='{self.nom_departement}', deleted={self.is_deleted})>"

    def __str__(self) -> str:
        """Représentation string lisible du département."""
        return self.nom_departement
