from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from app.db.connexion import Base
from sqlalchemy import ForeignKey,Date,DateTime,func,PrimaryKeyConstraint
from datetime import date


class Participation(Base):
    __tablename__ = "Participations"

    id_election: Mapped[int] = mapped_column(ForeignKey("Elections.id_election"))
    id_bureau: Mapped[int] = mapped_column(ForeignKey("BureauVotes.id_bureau"))
    nombre_electeur: Mapped[int] = mapped_column(default=0)
    nombre_votant: Mapped[int] = mapped_column(default=0)
    nombre_votant_hors_bureau: Mapped[int] = mapped_column(default=0)
    nombre_bulletin_null: Mapped[int] = mapped_column(default=0)
    nombre_suffrage: Mapped[int] = mapped_column(default=0)
    date_election: Mapped[date] = mapped_column(Date,nullable=False,default=date.today())
    created_at : Mapped[date] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)

    __table_args__=(
        PrimaryKeyConstraint("id_election","id_bureau","date_election",name="pk_participation"),
    )