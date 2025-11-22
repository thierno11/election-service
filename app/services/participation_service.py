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
    StatistiquesParticipationListe,
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


def get_all_participations(page,limit,db: Session) -> List[ParticipationReponse]:
    """
    Récupère toutes les participations.

    Args:
        db: Session de base de données

    Returns:
        List[ParticipationReponse]: Liste des participations

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        offset = (page-1)*limit
        participations = db.query(Participation).offset(offset).limit(limit).all()
        total = db.query(Participation).count()

        # Conversion en objets ParticipationReponse
        result = []
        for participation in participations:
            participation_response = ParticipationReponse(
                id_election=participation.id_election,
                id_bureau=participation.id_bureau,
                nombre_electeur=participation.nombre_electeur,
                nombre_votant=participation.nombre_votant,
                nombre_votant_hors_bureau=participation.nombre_votant_hors_bureau,
                nombre_bulletin_null=participation.nombre_bulletin_null,
                nombre_suffrage=participation.nombre_suffrage,
                date_election=participation.date_election,
                created_at=participation.created_at
            )
            result.append(participation_response)

        logger.info(f"Récupération de {len(result)} participations")
        return {"data":result,"total":total}

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des participations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des participations"
        )


def get_participation_by_keys(
    id_election: int,
    id_bureau: int,
    date_election: date,
    db: Session
) -> Optional[Participation]:
    """
    Récupère une participation par ses clés primaires.

    Args:
        id_election: ID de l'élection
        id_bureau: ID du bureau
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Optional[Participation]: La participation trouvée ou None
    """
    try:
        return db.query(Participation).filter(
            and_(
                Participation.id_election == id_election,
                Participation.id_bureau == id_bureau,
                Participation.date_election == date_election
            )
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de la participation: {e}")
        return None


def update_participation(
    id_election: int,
    id_bureau: int,
    date_election: date,
    participation_request: ParticipationSchema,
    db: Session
) -> Participation:
    """
    Met à jour une participation existante.

    Args:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau
        date_election: Date de l'élection
        participation_request: Nouvelles données de la participation
        db: Session de base de données

    Returns:
        Participation: La participation mise à jour

    Raises:
        HTTPException: Si la participation n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le bureau existe
        bureau = db.query(BureauVote).filter(
            BureauVote.id_bureau == id_bureau
        ).first()

        if not bureau:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau avec l'ID {id_bureau} introuvable"
            )

        # Vérifier si la participation existe
        participation = get_participation_by_keys(election.id_election, bureau.id_bureau, date_election, db)
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participation introuvable pour cette élection, bureau et date"
            )

        # Mettre à jour les champs (sauf les clés primaires)
        participation.nombre_electeur = participation_request.nombre_electeur
        participation.nombre_votant = participation_request.nombre_votant
        participation.nombre_votant_hors_bureau = participation_request.nombre_votant_hors_bureau
        participation.nombre_bulletin_null = participation_request.nombre_bulletin_null
        participation.nombre_suffrage = participation_request.nombre_suffrage

        db.commit()
        db.refresh(participation)

        logger.info(f"Participation mise à jour pour élection {election.id_election}, bureau {bureau.id_bureau}")
        return participation

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la mise à jour de la participation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def delete_participation(
    id_election: int,
    id_bureau: int,
    date_election: date,
    db: Session
) -> Dict[str, str]:
    """
    Supprime une participation existante.

    Args:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si la participation n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le bureau existe
        bureau = db.query(BureauVote).filter(
            BureauVote.id_bureau == id_bureau
        ).first()

        if not bureau:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau avec l'ID {id_bureau} introuvable"
            )

        # Vérifier si la participation existe
        participation = get_participation_by_keys(election.id_election, bureau.id_bureau, date_election, db)
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participation introuvable pour cette élection, bureau et date"
            )

        # Supprimer la participation
        db.delete(participation)
        db.commit()

        logger.info(f"Participation supprimée avec succès pour élection {election.id_election}, bureau {bureau.id_bureau}")
        return {"message": f"Participation supprimée avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression de la participation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
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


def get_statistiques_nationales(
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation nationales.
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

        query = db.query(
            func.sum(Participation.nombre_electeur).label('total_electeurs'),
            func.sum(Participation.nombre_votant).label('total_votants'),
            func.sum(Participation.nombre_votant_hors_bureau).label('total_votants_hors_bureau'),
            func.sum(Participation.nombre_bulletin_null).label('total_bulletins_nuls'),
            func.sum(Participation.nombre_suffrage).label('total_suffrages'),
        ).filter(
            and_(
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
        logger.error(f"Erreur lors du calcul des statistiques nationales: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_bureau_specifique(
    id_bureau: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation pour un bureau spécifique.
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

        # Vérifier que le bureau existe
        bureau = db.query(BureauVote).filter(
            BureauVote.id_bureau == id_bureau
        ).first()

        if not bureau:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau avec l'ID {id_bureau} introuvable"
            )

        # Récupérer la participation pour ce bureau
        participation = db.query(Participation).filter(
            and_(
                Participation.id_bureau == id_bureau,
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).first()

        if not participation:
            # Bureau sans participation pour cette élection/date
            stat = StatistiquesParticipation(
                total_electeurs=0,
                total_votants=0,
                total_votants_hors_bureau=0,
                total_bulletins_nuls=0,
                total_suffrages=0,
                taux_participation=0.0,
                taux_suffrages_valides=0.0
            )
        else:
            stat = StatistiquesParticipation(
                total_electeurs=participation.nombre_electeur,
                total_votants=participation.nombre_votant,
                total_votants_hors_bureau=participation.nombre_votant_hors_bureau,
                total_bulletins_nuls=participation.nombre_bulletin_null,
                total_suffrages=participation.nombre_suffrage,
                taux_participation=_calculer_taux_participation(
                    participation.nombre_votant,
                    participation.nombre_electeur
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    participation.nombre_suffrage,
                    participation.nombre_votant
                )
            )

        return stat

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques pour le bureau {id_bureau}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_centre_specifique(
    id_centre: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation pour un centre spécifique.
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

        # Vérifier que le centre existe
        centre = db.query(CentreVote).filter(
            CentreVote.id_centre == id_centre
        ).first()

        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre de vote avec l'ID {id_centre} introuvable"
            )

        query = db.query(
            func.sum(Participation.nombre_electeur).label('total_electeurs'),
            func.sum(Participation.nombre_votant).label('total_votants'),
            func.sum(Participation.nombre_votant_hors_bureau).label('total_votants_hors_bureau'),
            func.sum(Participation.nombre_bulletin_null).label('total_bulletins_nuls'),
            func.sum(Participation.nombre_suffrage).label('total_suffrages'),
        ).join(
            BureauVote, Participation.id_bureau == BureauVote.id_bureau
        ).filter(
            and_(
                BureauVote.id_centre == id_centre,
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
            )
        )

        return stat

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques pour le centre {id_centre}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_commune_specifique(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation pour une commune spécifique.
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

        # Vérifier que la commune existe
        commune = db.query(Commune).filter(
            Commune.id_commune == id_commune
        ).first()

        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune avec l'ID {id_commune} introuvable"
            )

        query = db.query(
            func.sum(Participation.nombre_electeur).label('total_electeurs'),
            func.sum(Participation.nombre_votant).label('total_votants'),
            func.sum(Participation.nombre_votant_hors_bureau).label('total_votants_hors_bureau'),
            func.sum(Participation.nombre_bulletin_null).label('total_bulletins_nuls'),
            func.sum(Participation.nombre_suffrage).label('total_suffrages'),
        ).join(
            BureauVote, Participation.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).filter(
            and_(
                CentreVote.id_commune == id_commune,
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
        logger.error(f"Erreur lors du calcul des statistiques pour la commune {id_commune}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_departement_specifique(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation pour un département spécifique.
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

        # Vérifier que le département existe
        departement = db.query(Departement).filter(
            Departement.id_departement == id_departement
        ).first()

        if not departement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec l'ID {id_departement} introuvable"
            )

        query = db.query(
            func.sum(Participation.nombre_electeur).label('total_electeurs'),
            func.sum(Participation.nombre_votant).label('total_votants'),
            func.sum(Participation.nombre_votant_hors_bureau).label('total_votants_hors_bureau'),
            func.sum(Participation.nombre_bulletin_null).label('total_bulletins_nuls'),
            func.sum(Participation.nombre_suffrage).label('total_suffrages'),
        ).join(
            BureauVote, Participation.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).join(
            Commune, CentreVote.id_commune == Commune.id_commune
        ).filter(
            and_(
                Commune.id_departement == id_departement,
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
        logger.error(f"Erreur lors du calcul des statistiques pour le département {id_departement}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
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


def get_statistiques_participation_repartition_regions(
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation avec répartition par région.
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

        # Requête pour récupérer les statistiques par région
        query = db.query(
            Region.id_region,
            Region.nom_region,
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
        ).join(
            Region, Departement.id_region == Region.id_region
        ).filter(
            and_(
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).group_by(Region.id_region, Region.nom_region).all()

        # Créer les statistiques par région
        statistiques_regions = {}
        for row in query:
            stat_region = StatistiquesParticipation(
                total_electeurs=row.total_electeurs or 0,
                total_votants=row.total_votants or 0,
                total_votants_hors_bureau=row.total_votants_hors_bureau or 0,
                total_bulletins_nuls=row.total_bulletins_nuls or 0,
                total_suffrages=row.total_suffrages or 0,
                taux_participation=_calculer_taux_participation(
                    row.total_votants or 0,
                    row.total_electeurs or 0
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    row.total_suffrages or 0,
                    row.total_votants or 0
                )
            )
            statistiques_regions[row.nom_region] = stat_region

        return statistiques_regions

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de participation par région: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_participation_repartition_departements(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation avec répartition par département pour une région.
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

        # Requête pour récupérer les statistiques par département de cette région
        query = db.query(
            Departement.id_departement,
            Departement.nom_departement,
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
        ).group_by(Departement.id_departement, Departement.nom_departement).all()

        # Créer les statistiques par département
        statistiques_departements = {}
        for row in query:
            stat_departement = StatistiquesParticipation(
                total_electeurs=row.total_electeurs or 0,
                total_votants=row.total_votants or 0,
                total_votants_hors_bureau=row.total_votants_hors_bureau or 0,
                total_bulletins_nuls=row.total_bulletins_nuls or 0,
                total_suffrages=row.total_suffrages or 0,
                taux_participation=_calculer_taux_participation(
                    row.total_votants or 0,
                    row.total_electeurs or 0
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    row.total_suffrages or 0,
                    row.total_votants or 0
                )
            )
            statistiques_departements[row.nom_departement] = stat_departement

        return statistiques_departements

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de participation par département: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_participation_repartition_communes(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation avec répartition par commune pour un département.
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

        # Vérifier que le département existe
        departement = db.query(Departement).filter(
            Departement.id_departement == id_departement
        ).first()

        if not departement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec l'ID {id_departement} introuvable"
            )

        # Requête pour récupérer les statistiques par commune de ce département
        query = db.query(
            Commune.id_commune,
            Commune.nom_commune,
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
        ).filter(
            and_(
                Commune.id_departement == id_departement,
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).group_by(Commune.id_commune, Commune.nom_commune).all()

        # Créer les statistiques par commune
        statistiques_communes = {}
        for row in query:
            stat_commune = StatistiquesParticipation(
                total_electeurs=row.total_electeurs or 0,
                total_votants=row.total_votants or 0,
                total_votants_hors_bureau=row.total_votants_hors_bureau or 0,
                total_bulletins_nuls=row.total_bulletins_nuls or 0,
                total_suffrages=row.total_suffrages or 0,
                taux_participation=_calculer_taux_participation(
                    row.total_votants or 0,
                    row.total_electeurs or 0
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    row.total_suffrages or 0,
                    row.total_votants or 0
                )
            )
            statistiques_communes[row.nom_commune] = stat_commune

        return statistiques_communes

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de participation par commune: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_participation_repartition_centres(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation avec répartition par centre pour une commune.
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

        # Vérifier que la commune existe
        commune = db.query(Commune).filter(
            Commune.id_commune == id_commune
        ).first()

        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune avec l'ID {id_commune} introuvable"
            )

        # Requête pour récupérer les statistiques par centre de cette commune
        query = db.query(
            CentreVote.id_centre,
            CentreVote.nom_centre,
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
        ).filter(
            and_(
                CentreVote.id_commune == id_commune,
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).group_by(CentreVote.id_centre, CentreVote.nom_centre).all()

        # Créer les statistiques par centre
        statistiques_centres = {}
        for row in query:
            stat_centre = StatistiquesParticipation(
                total_electeurs=row.total_electeurs or 0,
                total_votants=row.total_votants or 0,
                total_votants_hors_bureau=row.total_votants_hors_bureau or 0,
                total_bulletins_nuls=row.total_bulletins_nuls or 0,
                total_suffrages=row.total_suffrages or 0,
                taux_participation=_calculer_taux_participation(
                    row.total_votants or 0,
                    row.total_electeurs or 0
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    row.total_suffrages or 0,
                    row.total_votants or 0
                )
            )
            statistiques_centres[row.nom_centre] = stat_centre

        return statistiques_centres

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de participation par centre: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_participation_repartition_bureaux(
    id_centre: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de participation avec répartition par bureau pour un centre.
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

        # Vérifier que le centre existe
        centre = db.query(CentreVote).filter(
            CentreVote.id_centre == id_centre
        ).first()

        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre de vote avec l'ID {id_centre} introuvable"
            )

        # Requête pour récupérer les statistiques par bureau de ce centre
        query = db.query(
            BureauVote.id_bureau,
            BureauVote.numero_bureau,
            Participation.nombre_electeur,
            Participation.nombre_votant,
            Participation.nombre_votant_hors_bureau,
            Participation.nombre_bulletin_null,
            Participation.nombre_suffrage
        ).join(
            BureauVote, Participation.id_bureau == BureauVote.id_bureau
        ).filter(
            and_(
                BureauVote.id_centre == id_centre,
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        ).order_by(BureauVote.numero_bureau).all()

        # Créer les statistiques par bureau
        statistiques_bureaux = {}
        for row in query:
            stat_bureau = StatistiquesParticipation(
                total_electeurs=row.nombre_electeur or 0,
                total_votants=row.nombre_votant or 0,
                total_votants_hors_bureau=row.nombre_votant_hors_bureau or 0,
                total_bulletins_nuls=row.nombre_bulletin_null or 0,
                total_suffrages=row.nombre_suffrage or 0,
                taux_participation=_calculer_taux_participation(
                    row.nombre_votant or 0,
                    row.nombre_electeur or 0
                ),
                taux_suffrages_valides=_calculer_taux_suffrages_valides(
                    row.nombre_suffrage or 0,
                    row.nombre_votant or 0
                )
            )
            statistiques_bureaux[f"Bureau {row.numero_bureau}"] = stat_bureau

        return statistiques_bureaux

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de participation par bureau: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_evolution_votants_temporelle(
    id_election: int,
    date_election: date,
    db: Session,
    interval_minutes: int = 15
):
    """
    Récupère l'évolution du nombre de votants agrégée par tranche de temps paramétrable.
    interval_minutes peut être : 15, 30, 60, 120
    """
    # Vérifier que l'intervalle demandé est valide
    if interval_minutes not in [15, 30, 60, 120]:
        raise HTTPException(
            status_code=400,
            detail="Intervalle non valide. Choisissez parmi: 15, 30, 60, 120 minutes."
        )

    # Vérifier que l'élection existe
    election = db.query(Election).filter(
        Election.id_election == id_election
    ).first()

    if not election:
        raise HTTPException(
            status_code=404,
            detail=f"Élection avec l'ID {id_election} introuvable"
        )

    # Construire l'intervalle SQL correct
    interval_sql = f"interval '{interval_minutes} minutes'"

    # Expression pour grouper par tranche de temps
    intervalle_expr = (
        func.date_trunc(
            'minute',
            func.date_trunc('hour', Participation.created_at)
            + func.floor(
                func.extract('epoch', Participation.created_at) / (interval_minutes * 60)
            ) * text(interval_sql)
        ).label("intervalle")
    )

    participations_query = (
        db.query(
            intervalle_expr,
            func.sum(Participation.nombre_votant).label("total_votants")
        )
        .filter(
            and_(
                Participation.id_election == election.id_election,
                Participation.date_election == date_election
            )
        )
        .group_by(intervalle_expr)
        .order_by(intervalle_expr)
        .all()
    )

    # Construire l'évolution cumulée
    evolution = []
    cumul = 0
    for row in participations_query:
        cumul += row.total_votants
        evolution.append({
            "intervalle": row.intervalle,
            "nouveaux_votants": row.total_votants,
            "cumul_votants": cumul
        })

    return {
        "id_election": id_election,
        "date_election": date_election,
        "interval_minutes": interval_minutes,
        "total_votants": cumul,
        "nombre_intervalles": len(evolution),
        "evolution": evolution
    }


def get_evolution_votants_temporelle_region(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session,
    interval_minutes: int = 15
):
    """
    Récupère l'évolution du nombre de votants agrégée par tranche de temps pour une région spécifique.
    interval_minutes peut être : 15, 30, 60, 120
    """
    try:
        # Vérifier que l'intervalle demandé est valide
        if interval_minutes not in [15, 30, 60, 120]:
            raise HTTPException(
                status_code=400,
                detail="Intervalle non valide. Choisissez parmi: 15, 30, 60, 120 minutes."
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=404,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la région existe
        region = db.query(Region).filter(
            Region.id_region == id_region
        ).first()

        if not region:
            raise HTTPException(
                status_code=404,
                detail=f"Région avec l'ID {id_region} introuvable"
            )

        # Construire l'intervalle SQL correct
        interval_sql = f"interval '{interval_minutes} minutes'"

        # Expression pour grouper par tranche de temps
        intervalle_expr = (
            func.date_trunc(
                'minute',
                func.date_trunc('hour', Participation.created_at)
                + func.floor(
                    func.extract('epoch', Participation.created_at) / (interval_minutes * 60)
                ) * text(interval_sql)
            ).label("intervalle")
        )

        # Requête avec jointures pour filtrer par région
        participations_query = (
            db.query(
                intervalle_expr,
                func.sum(Participation.nombre_votant).label("total_votants")
            )
            .join(BureauVote, Participation.id_bureau == BureauVote.id_bureau)
            .join(CentreVote, BureauVote.id_centre == CentreVote.id_centre)
            .join(Commune, CentreVote.id_commune == Commune.id_commune)
            .join(Departement, Commune.id_departement == Departement.id_departement)
            .filter(
                and_(
                    Departement.id_region == id_region,
                    Participation.id_election == election.id_election,
                    Participation.date_election == date_election
                )
            )
            .group_by(intervalle_expr)
            .order_by(intervalle_expr)
            .all()
        )

        # Construire l'évolution cumulée
        evolution = []
        cumul = 0
        for row in participations_query:
            cumul += row.total_votants
            evolution.append({
                "intervalle": row.intervalle,
                "nouveaux_votants": row.total_votants,
                "cumul_votants": cumul
            })

        return {
            "id_region": id_region,
            "nom_region": region.nom_region,
            "id_election": id_election,
            "date_election": date_election,
            "interval_minutes": interval_minutes,
            "total_votants": cumul,
            "nombre_intervalles": len(evolution),
            "evolution": evolution
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul de l'évolution temporelle des votants pour la région {id_region}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul de l'évolution temporelle"
        )


def get_evolution_votants_temporelle_departement(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session,
    interval_minutes: int = 15
):
    """
    Récupère l'évolution du nombre de votants agrégée par tranche de temps pour un département spécifique.
    interval_minutes peut être : 15, 30, 60, 120
    """
    try:
        # Vérifier que l'intervalle demandé est valide
        if interval_minutes not in [15, 30, 60, 120]:
            raise HTTPException(
                status_code=400,
                detail="Intervalle non valide. Choisissez parmi: 15, 30, 60, 120 minutes."
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=404,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le département existe
        departement = db.query(Departement).filter(
            Departement.id_departement == id_departement
        ).first()

        if not departement:
            raise HTTPException(
                status_code=404,
                detail=f"Département avec l'ID {id_departement} introuvable"
            )

        # Construire l'intervalle SQL correct
        interval_sql = f"interval '{interval_minutes} minutes'"

        # Expression pour grouper par tranche de temps
        intervalle_expr = (
            func.date_trunc(
                'minute',
                func.date_trunc('hour', Participation.created_at)
                + func.floor(
                    func.extract('epoch', Participation.created_at) / (interval_minutes * 60)
                ) * text(interval_sql)
            ).label("intervalle")
        )

        # Requête avec jointures pour filtrer par département
        participations_query = (
            db.query(
                intervalle_expr,
                func.sum(Participation.nombre_votant).label("total_votants")
            )
            .join(BureauVote, Participation.id_bureau == BureauVote.id_bureau)
            .join(CentreVote, BureauVote.id_centre == CentreVote.id_centre)
            .join(Commune, CentreVote.id_commune == Commune.id_commune)
            .filter(
                and_(
                    Commune.id_departement == id_departement,
                    Participation.id_election == election.id_election,
                    Participation.date_election == date_election
                )
            )
            .group_by(intervalle_expr)
            .order_by(intervalle_expr)
            .all()
        )

        # Construire l'évolution cumulée
        evolution = []
        cumul = 0
        for row in participations_query:
            cumul += row.total_votants
            evolution.append({
                "intervalle": row.intervalle,
                "nouveaux_votants": row.total_votants,
                "cumul_votants": cumul
            })

        return {
            "id_departement": id_departement,
            "nom_departement": departement.nom_departement,
            "id_election": id_election,
            "date_election": date_election,
            "interval_minutes": interval_minutes,
            "total_votants": cumul,
            "nombre_intervalles": len(evolution),
            "evolution": evolution
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul de l'évolution temporelle des votants pour le département {id_departement}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul de l'évolution temporelle"
        )


def get_evolution_votants_temporelle_commune(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session,
    interval_minutes: int = 15
):
    """
    Récupère l'évolution du nombre de votants agrégée par tranche de temps pour une commune spécifique.
    interval_minutes peut être : 15, 30, 60, 120
    """
    try:
        # Vérifier que l'intervalle demandé est valide
        if interval_minutes not in [15, 30, 60, 120]:
            raise HTTPException(
                status_code=400,
                detail="Intervalle non valide. Choisissez parmi: 15, 30, 60, 120 minutes."
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=404,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la commune existe
        commune = db.query(Commune).filter(
            Commune.id_commune == id_commune
        ).first()

        if not commune:
            raise HTTPException(
                status_code=404,
                detail=f"Commune avec l'ID {id_commune} introuvable"
            )

        # Construire l'intervalle SQL correct
        interval_sql = f"interval '{interval_minutes} minutes'"

        # Expression pour grouper par tranche de temps
        intervalle_expr = (
            func.date_trunc(
                'minute',
                func.date_trunc('hour', Participation.created_at)
                + func.floor(
                    func.extract('epoch', Participation.created_at) / (interval_minutes * 60)
                ) * text(interval_sql)
            ).label("intervalle")
        )

        # Requête avec jointures pour filtrer par commune
        participations_query = (
            db.query(
                intervalle_expr,
                func.sum(Participation.nombre_votant).label("total_votants")
            )
            .join(BureauVote, Participation.id_bureau == BureauVote.id_bureau)
            .join(CentreVote, BureauVote.id_centre == CentreVote.id_centre)
            .filter(
                and_(
                    CentreVote.id_commune == id_commune,
                    Participation.id_election == election.id_election,
                    Participation.date_election == date_election
                )
            )
            .group_by(intervalle_expr)
            .order_by(intervalle_expr)
            .all()
        )

        # Construire l'évolution cumulée
        evolution = []
        cumul = 0
        for row in participations_query:
            cumul += row.total_votants
            evolution.append({
                "intervalle": row.intervalle,
                "nouveaux_votants": row.total_votants,
                "cumul_votants": cumul
            })

        return {
            "id_commune": id_commune,
            "nom_commune": commune.nom_commune,
            "id_election": id_election,
            "date_election": date_election,
            "interval_minutes": interval_minutes,
            "total_votants": cumul,
            "nombre_intervalles": len(evolution),
            "evolution": evolution
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul de l'évolution temporelle des votants pour la commune {id_commune}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul de l'évolution temporelle"
        )


def get_evolution_votants_temporelle_centre(
    id_centre: int,
    id_election: int,
    date_election: date,
    db: Session,
    interval_minutes: int = 15
):
    """
    Récupère l'évolution du nombre de votants agrégée par tranche de temps pour un centre de vote spécifique.
    interval_minutes peut être : 15, 30, 60, 120
    """
    try:
        # Vérifier que l'intervalle demandé est valide
        if interval_minutes not in [15, 30, 60, 120]:
            raise HTTPException(
                status_code=400,
                detail="Intervalle non valide. Choisissez parmi: 15, 30, 60, 120 minutes."
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=404,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le centre existe
        centre = db.query(CentreVote).filter(
            CentreVote.id_centre == id_centre
        ).first()

        if not centre:
            raise HTTPException(
                status_code=404,
                detail=f"Centre de vote avec l'ID {id_centre} introuvable"
            )

        # Construire l'intervalle SQL correct
        interval_sql = f"interval '{interval_minutes} minutes'"

        # Expression pour grouper par tranche de temps
        intervalle_expr = (
            func.date_trunc(
                'minute',
                func.date_trunc('hour', Participation.created_at)
                + func.floor(
                    func.extract('epoch', Participation.created_at) / (interval_minutes * 60)
                ) * text(interval_sql)
            ).label("intervalle")
        )

        # Requête avec jointures pour filtrer par centre
        participations_query = (
            db.query(
                intervalle_expr,
                func.sum(Participation.nombre_votant).label("total_votants")
            )
            .join(BureauVote, Participation.id_bureau == BureauVote.id_bureau)
            .filter(
                and_(
                    BureauVote.id_centre == id_centre,
                    Participation.id_election == election.id_election,
                    Participation.date_election == date_election
                )
            )
            .group_by(intervalle_expr)
            .order_by(intervalle_expr)
            .all()
        )

        # Construire l'évolution cumulée
        evolution = []
        cumul = 0
        for row in participations_query:
            cumul += row.total_votants
            evolution.append({
                "intervalle": row.intervalle,
                "nouveaux_votants": row.total_votants,
                "cumul_votants": cumul
            })

        return {
            "id_centre": id_centre,
            "nom_centre": centre.nom_centre,
            "id_election": id_election,
            "date_election": date_election,
            "interval_minutes": interval_minutes,
            "total_votants": cumul,
            "nombre_intervalles": len(evolution),
            "evolution": evolution
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul de l'évolution temporelle des votants pour le centre {id_centre}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul de l'évolution temporelle"
        )
