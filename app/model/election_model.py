"""Modèle SQLAlchemy pour les élections."""

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.connexion import Base
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.model.inscription_election_model import InscriptionElection


class Election(Base):
    """
    Modèle représentant une élection.

    Attributes:
        id_election: Identifiant unique de l'élection
        type_election: Type d'élection (présidentielle, législative, etc.)
        is_deleted: Indique si l'élection est supprimée (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour de l'enregistrement
        inscriptions: Liste des inscriptions de candidats à cette élection
    """

    __tablename__ = "Elections"

    id_election: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Identifiant unique de l'élection"
    )

    type_election: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Type d'élection (présidentielle, législative, municipale, etc.)"
    )

    # Suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si l'élection est supprimée (soft delete)"
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

    # Relation bidirectionnelle avec InscriptionElection
    inscriptions: Mapped[List["InscriptionElection"]] = relationship(
        "InscriptionElection",
        back_populates="election",
        lazy="select"
    )

    def __repr__(self) -> str:
        """Représentation string de l'élection."""
        return f"<Election(id={self.id_election}, type='{self.type_election}', deleted={self.is_deleted})>"

    def __str__(self) -> str:
        """Représentation lisible de l'élection."""
        return self.type_election
