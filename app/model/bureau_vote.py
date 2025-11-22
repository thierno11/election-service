"""Modèle SQLAlchemy pour les bureaux de vote."""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, UniqueConstraint, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.connexion import Base

if TYPE_CHECKING:
    from app.model.centres_votes_model import CentreVote


class BureauVote(Base):
    """
    Modèle représentant un bureau de vote.

    Attributes:
        id_bureau: Identifiant unique du bureau de vote
        numero_bureau: Numéro du bureau dans le centre
        implantation: Localisation/adresse du bureau
        id_centre: Clé étrangère vers le centre de vote
        is_deleted: Indique si le bureau est supprimé (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour de l'enregistrement
        centre_vote: Centre de vote auquel appartient ce bureau
    """

    __tablename__ = "BureauVotes"

    id_bureau: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique du bureau de vote"
    )

    numero_bureau: Mapped[int] = mapped_column(
        nullable=False,
        comment="Numéro du bureau dans le centre"
    )

    implantation: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Localisation/adresse du bureau"
    )

    id_centre: Mapped[int] = mapped_column(
        ForeignKey("CentreVotes.id_centre", ondelete="CASCADE"),
        nullable=False,
        comment="Identifiant du centre de vote"
    )

    # Suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si le bureau est supprimé (soft delete)"
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
    centre_vote: Mapped["CentreVote"] = relationship(
        "CentreVote",
        back_populates="bureaux_vote",
        lazy="select"
    )

    __table_args__ = (
        UniqueConstraint(
            "numero_bureau", "id_centre",
            name="uk_bureau_numero_centre",
            comment="Un bureau avec un numéro donné ne peut exister qu'une fois par centre"
        ),
    )

    def __repr__(self) -> str:
        """Représentation string du bureau de vote."""
        return (
            f"<BureauVote(id={self.id_bureau}, numero={self.numero_bureau}, "
            f"deleted={self.is_deleted})>"
        )

    def __str__(self) -> str:
        """Représentation string lisible du bureau de vote."""
        return f"Bureau {self.numero_bureau}"
