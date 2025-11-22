"""Modèle SQLAlchemy pour les centres de vote."""

from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, UniqueConstraint, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.connexion import Base

if TYPE_CHECKING:
    from app.model.commune_model import Commune
    from  app.model.bureau_vote import BureauVote


class CentreVote(Base):
    """
    Modèle représentant un centre de vote.

    Attributes:
        id_centre: Identifiant unique du centre de vote
        nom_centre: Nom du centre de vote
        id_commune: Clé étrangère vers la commune
        is_deleted: Indique si le centre est supprimé (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour
        commune: Commune à laquelle appartient ce centre
        bureaux_vote: Liste des bureaux de vote dans ce centre
    """

    __tablename__ = "CentreVotes"

    id_centre: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique du centre de vote"
    )

    nom_centre: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Nom du centre de vote"
    )

    id_commune: Mapped[int] = mapped_column(
        ForeignKey("Communes.id_commune", ondelete="CASCADE"),
        nullable=False,
        comment="Identifiant de la commune"
    )

    # Indicateur de suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si le centre est supprimé (soft delete)"
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
    commune: Mapped["Commune"] = relationship(
        "Commune",
        back_populates="centres_vote",
        lazy="select"
    )

    bureaux_vote: Mapped[List["BureauVote"]] = relationship(
        "BureauVote",
        back_populates="centre_vote",
        lazy="select",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "nom_centre", "id_commune",
            name="uk_centre_vote_commune",
            comment="Un centre avec un nom donné ne peut exister qu'une fois par commune"
        ),
    )

    def __repr__(self) -> str:
        """Représentation string du centre de vote."""
        return (
            f"<CentreVote(id={self.id_centre}, nom='{self.nom_centre}', "
            f"deleted={self.is_deleted})>"
        )

    def __str__(self) -> str:
        """Représentation string lisible du centre de vote."""
        return self.nom_centre
