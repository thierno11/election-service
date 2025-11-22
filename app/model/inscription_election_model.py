"""Modèle SQLAlchemy pour les inscriptions d'élection."""

from sqlalchemy import ForeignKey, Date, PrimaryKeyConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.connexion import Base
from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.election_model import Election
    from app.model.candidat_model import Candidat


class InscriptionElection(Base):
    """
    Modèle représentant l'inscription d'un candidat à une élection.

    Attributes:
        id_election: Identifiant de l'élection
        id_candidat: Identifiant du candidat
        date_election: Date de l'élection
        created_at: Date et heure de création de l'inscription
    """
    __tablename__ = "InscriptionElections"

    id_election: Mapped[int] = mapped_column(ForeignKey("Elections.id_election"))
    id_candidat: Mapped[int] = mapped_column(ForeignKey("Candidats.id_candidat"))
    date_election: Mapped[date] = mapped_column(Date, default=date.today())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations bidirectionnelles
    election: Mapped["Election"] = relationship("Election", back_populates="inscriptions")
    candidat: Mapped["Candidat"] = relationship("Candidat", back_populates="inscriptions")

    __table_args__ = (
        PrimaryKeyConstraint("id_election", "id_candidat", "date_election", name="pk_inscription_elections"),
    )

    def __repr__(self) -> str:
        """Représentation string de l'inscription d'élection."""
        return f"<InscriptionElection(id_election={self.id_election}, id_candidat={self.id_candidat}, date_election='{self.date_election}')>"

    def __str__(self) -> str:
        """Représentation string lisible de l'inscription d'élection."""
        return f"Inscription - Élection {self.id_election}, Candidat {self.id_candidat}, Date {self.date_election}"