from sqlalchemy import ForeignKey,Date,PrimaryKeyConstraint,DateTime,func
from sqlalchemy.orm import  Mapped, mapped_column
from app.db.connexion import Base
from datetime import date, datetime


class ResultatVote(Base):
    __tablename__ = "ResultatVotes"

    id_election: Mapped[int] = mapped_column(ForeignKey("Elections.id_election"))
    id_bureau: Mapped[int] = mapped_column(ForeignKey("BureauVotes.id_bureau"))
    id_candidat: Mapped[int] = mapped_column(ForeignKey("Candidats.id_candidat"))
    date_election: Mapped[date] = mapped_column(Date,default=date.today())
    voix: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__=(
        PrimaryKeyConstraint("id_election","id_bureau","id_candidat","date_election",name="pk_resultats_votes"),
    )
