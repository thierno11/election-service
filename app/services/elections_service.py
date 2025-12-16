"""Service pour la gestion des élections."""

import logging
from typing import Dict, List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, distinct
from fastapi import HTTPException, status

from app.model.election_model import Election
from app.model.inscription_election_model import InscriptionElection
from app.schema.election_schema import ElectionSchema, ElectionReponse

logger = logging.getLogger(__name__)


def create_election(election: ElectionSchema, db: Session) -> Election:
    """
    Crée une nouvelle élection.

    Args:
        election: Données de l'élection à créer
        db: Session de base de données

    Returns:
        Election: L'élection créée

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier si une élection avec le même type existe déjà
        existing = db.query(Election).filter(
            Election.type_election == election.type_election
        ).first()

        if existing:
            logger.warning(f"Tentative de création d'une élection avec un type existant: {election.type_election}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une élection de type '{election.type_election}' existe déjà"
            )

        # Créer l'élection
        db_election = Election(**election.model_dump())

        db.add(db_election)
        db.commit()
        db.refresh(db_election)

        logger.info(f"Élection créée avec succès (ID: {db_election.id_election})")
        return db_election

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création de l'élection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création de l'élection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_all_elections(db: Session) -> List[ElectionReponse]:
    """
    Récupère toutes les élections.

    Args:
        db: Session de base de données

    Returns:
        List[ElectionReponse]: Liste des élections

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        elections = db.query(Election).all()
        # Conversion en objets ElectionReponse
        result = []
        for election in elections:
            election_response = ElectionReponse(
                id_election=election.id_election,
                type_election=election.type_election
            )
            result.append(election_response)

        logger.info(f"Récupération de {len(result)} élections")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des élections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des élections"
        )


def get_election_by_id(election_id: int, db: Session) -> Optional[Election]:
    """
    Récupère une élection par son ID.

    Args:
        election_id: ID de l'élection
        db: Session de base de données

    Returns:
        Optional[Election]: L'élection trouvée ou None
    """
    try:
        return db.query(Election).filter(Election.id_election == election_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de l'élection {election_id}: {e}")
        return None


def update_election(election_id: int, election_request: ElectionSchema, db: Session) -> Election:
    """
    Met à jour une élection existante.

    Args:
        election_id: ID de l'élection à mettre à jour
        election_request: Nouvelles données de l'élection
        db: Session de base de données

    Returns:
        Election: L'élection mise à jour

    Raises:
        HTTPException: Si l'élection n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si l'élection existe
        election = get_election_by_id(election_id, db)
        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {election_id} introuvable"
            )

        # Mettre à jour les champs
        for field, value in election_request.model_dump().items():
            setattr(election, field, value)

        db.commit()
        db.refresh(election)

        logger.info(f"Élection mise à jour (ID: {election_id})")
        return election

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la mise à jour de l'élection {election_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la mise à jour de l'élection {election_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def delete_election(election_id: int, db: Session) -> Dict[str, str]:
    """
    Supprime une élection existante.

    Args:
        election_id: ID de l'élection à supprimer
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si l'élection n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si l'élection existe
        election = get_election_by_id(election_id, db)
        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {election_id} introuvable"
            )

        # Supprimer l'élection
        db.delete(election)
        db.commit()

        logger.info(f"Élection supprimée avec succès (ID: {election_id})")
        return {"message": f"Élection avec l'ID {election_id} supprimée avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression de l'élection {election_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_dates_election(election_id: int, db: Session) -> List[date]:
    """
    Récupère les dates distinctes d'une élection spécifique.

    Args:
        election_id: ID de l'élection
        db: Session de base de données

    Returns:
        List[date]: Liste des dates distinctes de l'élection

    Raises:
        HTTPException: Si l'élection n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier que l'élection existe
        election = get_election_by_id(election_id, db)
        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {election_id} introuvable"
            )

        # Récupérer les dates distinctes de cette élection depuis la table InscriptionElection
        dates = (
            db.query(distinct(InscriptionElection.date_election))
            .filter(InscriptionElection.id_election == election_id)
            .order_by(InscriptionElection.date_election)
            .all()
        )

        # Extraire les dates de la liste de tuples
        dates_list = [d[0] for d in dates]

        logger.info(f"Récupération de {len(dates_list)} dates distinctes pour l'élection {election_id}")
        return dates_list

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des dates pour l'élection {election_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des dates de l'élection"
        )
    


def get_dates(db: Session) -> List[date]:
    """
    Récupère les dates distinctes d'une élection spécifique.

    Args:
        election_id: ID de l'élection
        db: Session de base de données

    Returns:
        List[date]: Liste des dates distinctes de l'élection

    Raises:
        HTTPException: Si l'élection n'existe pas ou en cas d'erreur
    """
    try:
        # Récupérer les dates distinctes de cette élection depuis la table InscriptionElection
        dates = (
            db.query(distinct(InscriptionElection.date_election))
            .order_by(InscriptionElection.date_election)
            .all()
        )

        # Extraire les dates de la liste de tuples
        dates_list = [d[0] for d in dates]
        return dates_list

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des dates pour les élections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des dates de l'élection"
        )