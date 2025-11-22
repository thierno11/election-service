"""Modèle SQLAlchemy pour les communes."""

from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.connexion import Base

if TYPE_CHECKING:
    from app.model.departement_model import Departement
    from app.model.centres_votes_model import CentreVote


class Commune(Base):
    """
    Modèle représentant une commune administrative.

    Attributes:
        id_commune: Identifiant unique de la commune
        nom_commune: Nom de la commune (unique)
        id_departement: Clé étrangère vers le département parent
        is_deleted: Indique si la commune est supprimée (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour de l'enregistrement
        departement: Département auquel appartient cette commune
        centres_vote: Liste des centres de vote dans cette commune
    """

    __tablename__ = "Communes"

    id_commune: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique de la commune"
    )

    nom_commune: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Nom de la commune"
    )

    id_departement: Mapped[int] = mapped_column(
        ForeignKey("Departements.id_departement", ondelete="CASCADE"),
        nullable=False,
        comment="Identifiant du département parent"
    )

    # Suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si la commune est supprimée (soft delete)"
    )

    # Horodatage de création
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date de création de l'enregistrement"
    )

    # Horodatage de mise à jour
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Date de dernière mise à jour de l'enregistrement"
    )

    # Relations
    departement: Mapped["Departement"] = relationship(
        "Departement",
        back_populates="communes",
        lazy="select"
    )

    centres_vote: Mapped[List["CentreVote"]] = relationship(
        "CentreVote",
        back_populates="commune",
        lazy="select"
    )

    def __repr__(self) -> str:
        """Représentation string de la commune."""
        return f"<Commune(id={self.id_commune}, nom='{self.nom_commune}', deleted={self.is_deleted})>"

    def __str__(self) -> str:
        """Représentation string lisible de la commune."""
        return self.nom_commune
