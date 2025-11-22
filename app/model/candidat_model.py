from app.db.connexion import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Boolean, func, String
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.inscription_election_model import InscriptionElection


class Candidat(Base):
    """
    Modèle représentant un candidat.

    Attributes:
        id_candidat: Identifiant unique du candidat
        nom_candidat: Nom complet du candidat
        is_deleted: Indique si le candidat est supprimé (soft delete)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière mise à jour de l'enregistrement
        inscriptions: Liste des inscriptions du candidat aux élections
    """

    __tablename__ = "Candidats"

    id_candidat: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        nullable=False,
        comment="Identifiant unique du candidat"
    )

    nom_candidat: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        comment="Nom complet du candidat"
    )

    # Suppression logique
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indique si le candidat est supprimé (soft delete)"
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

    # Relation bidirectionnelle avec InscriptionElection
    inscriptions: Mapped[List["InscriptionElection"]] = relationship(
        "InscriptionElection",
        back_populates="candidat",
        lazy="select"
    )

    def __repr__(self) -> str:
        """Représentation textuelle du candidat."""
        return f"<Candidat(id={self.id_candidat}, nom='{self.nom_candidat}', deleted={self.is_deleted})>"

    def __str__(self) -> str:
        """Représentation lisible du candidat."""
        return self.nom_candidat
