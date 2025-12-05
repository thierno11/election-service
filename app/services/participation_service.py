"""Service pour la gestion des participations."""

import logging
from typing import Dict, List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, func, text
from fastapi import HTTPException, status
from app.services.commune_service import get_communes_by_nom_commune
from app.services.centre_votes_service import get_centre_by_nom_centre

from app.model.participation_model import Participation
from app.model.election_model import Election
from app.model.bureau_vote import BureauVote
from app.model.centres_votes_model import CentreVote
from app.model.commune_model import Commune
from app.model.departement_model import Departement
from app.model.region_model import Region
from app.schema.participation_schema import (
    ParticipationSchema,
    ParticipationReponse,
    StatistiquesParticipation,
)

logger = logging.getLogger(__name__)


def create_participation(participation: ParticipationSchema, db: Session) -> Participation:
    """
    Crée une nouvelle participation.

    Args:
        participation: Données de la participation à créer
        db: Session de base de données

    Returns:
        Participation: La participation créée

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Rechercher l'élection par son type
        election = db.query(Election).filter(
            Election.type_election == participation.type_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection de type '{participation.type_election}' introuvable"
            )
        commune = get_communes_by_nom_commune(participation.commune,db)
        print(commune)
        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune '{participation.commune}' introuvable")
        centre_communes = commune.centres_vote

        # Recherche avec correspondance partielle (insensible à la casse)
        centre_search = participation.centre.upper()
        centre = next((x for x in centre_communes if centre_search in x.nom_centre.upper()), None)

        print(centre)
        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre contenant '{participation.centre}' introuvable")

        new_centre = db.query(CentreVote).filter(CentreVote.id_centre == centre.id_centre).first()

        bureau_vote = next((x for x in new_centre.bureaux_vote if x.numero_bureau == participation.bureau), None)

        if not bureau_vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau numéro '{participation.bureau}' introuvable dans le centre '{participation.centre}'")


        # # Vérifier que le bureau existe
        # bureau = db.query(BureauVote).filter(
        #     BureauVote.id_bureau == participation.id_bureau
        # ).first()

        # if not bureau:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Bureau avec l'ID {participation.id_bureau} introuvable"
        #     )

        # Vérifier si une participation existe déjà pour cette combinaison
        existing = db.query(Participation).filter(
            and_(
                Participation.id_election == election.id_election,
                Participation.id_bureau == bureau_vote.id_bureau,
                Participation.date_election == participation.date_election
            )
        ).first()

        if existing:
            logger.warning(f"Tentative de création d'une participation existante pour élection {election.id_election}, bureau {bureau_vote.id_bureau}, date {participation.date_election}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Une participation existe déjà pour cette élection, bureau et date"
            )

        # Créer la participation avec les IDs trouvés
        db_participation = Participation(
            id_election=election.id_election,
            id_bureau=bureau_vote.id_bureau,
            nombre_electeur=participation.nombre_electeur,
            nombre_votant=participation.nombre_votant,
            nombre_votant_hors_bureau=participation.nombre_votant_hors_bureau,
            nombre_bulletin_null=participation.nombre_bulletin_null,
            nombre_suffrage=participation.nombre_suffrage,
            date_election=participation.date_election
        )

        db.add(db_participation)
        db.commit()
        db.refresh(db_participation)

        logger.info(f"Participation créée avec succès pour élection {db_participation.id_election}, bureau {db_participation.id_bureau}")
        return db_participation

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création de la participation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création de la participation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )

def get_statistiques_region_specifique(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation pour une région spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la région existe
        region = db.query(Region).filter(
            Region.id_region == id_region
        ).first()

        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Région avec l'ID {id_region} introuvable"
            )

        query = db.query(
            func.sum(Participation.nombre_electeur).label('total_electeurs'),
            func.sum(Participation.nombre_votant).label('total_votants'),
            func.sum(Participation.nombre_votant_hors_bureau).label('total_votants_hors_bureau'),
            func.sum(Participation.nombre_bulletin_null).label('total_bulletins_nuls'),
            func.sum(Participation.nombre_suffrage).label('total_suffrages'),
            func.count(Participation.id_bureau).label('nombre_bureaux')
        ).join(
            BureauVote, Participation.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).join(
            Commune, CentreVote.id_commune == Commune.id_commune
        ).join(
            Departement, Commune.id_departement == Departement.id_departement
        ).filter(
            and_(
                Departement.id_region == id_region,
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).first()

        stat = StatistiquesParticipation(
            total_electeurs=query.total_electeurs or 0,
            total_votants=query.total_votants or 0,
            total_votants_hors_bureau=query.total_votants_hors_bureau or 0,
            total_bulletins_nuls=query.total_bulletins_nuls or 0,
            total_suffrages=query.total_suffrages or 0,
            taux_participation=_calculer_taux_participation(
                query.total_votants or 0,
                query.total_electeurs or 0
            ),
            taux_suffrages_valides=_calculer_taux_suffrages_valides(
                query.total_suffrages or 0,
                query.total_votants or 0
            ),
        )

        return stat

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques pour la région {id_region}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )

def _calculer_taux_participation(total_votants: int, total_electeurs: int) -> float:
    """Calcule le taux de participation."""
    if total_electeurs == 0:
        return 0.0
    return round((total_votants / total_electeurs) * 100, 2)


def _calculer_taux_suffrages_valides(total_suffrages: int, total_votants: int) -> float:
    """Calcule le taux de suffrages valides."""
    if total_votants == 0:
        return 0.0
    return round((total_suffrages / total_votants) * 100, 2)
