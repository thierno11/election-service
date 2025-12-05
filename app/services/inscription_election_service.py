"""Service pour la gestion des inscriptions d'élection."""

import logging
from typing import Dict, List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.model.inscription_election_model import InscriptionElection
from app.model.election_model import Election
from app.model.candidat_model import Candidat
from app.schema.inscription_election_schema import (
    InscriptionElectionReponse,
    InscriptionElectionAvecDetails,
    InscriptionElectionBulkSchema
)

logger = logging.getLogger(__name__)

def is_inscription_exists(id_candidat: int, id_election: int, date, db: Session):
    inscription = (
        db.query(InscriptionElection)
        .filter(
            InscriptionElection.id_election == id_election,
            InscriptionElection.id_candidat == id_candidat,
            InscriptionElection.date_election == date
        )
        .first()
    )
    return inscription is not None



def create_inscriptions_bulk(inscriptions_bulk: InscriptionElectionBulkSchema, db: Session) -> List[InscriptionElection]:
    """
    Crée plusieurs inscriptions d'élection en une seule opération.

    Args:
        inscriptions_bulk: Données des inscriptions à créer en masse
        db: Session de base de données

    Returns:
        List[InscriptionElection]: Liste des inscriptions créées

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Rechercher l'ID de l'élection
        election = db.query(Election).filter(
            Election.id_election == inscriptions_bulk.id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {inscriptions_bulk.id_election} introuvable"
            )

        created_inscriptions = []
        candidats_traites = set()  # Pour éviter les doublons dans la même requête
        for item in inscriptions_bulk.candidats:
            # Rechercher l'ID du candidat
            candidat = db.query(Candidat).filter(
                Candidat.id_candidat == item.id_candidat
            ).first()

            if not candidat:
                logger.warning(f"Candidat '{item.id_candidat}' introuvable, ignoré")
                continue  # Ignorer ce candidat et continuer

            # Vérifier si une inscription existe déjà
            existing = is_inscription_exists(candidat.id_candidat,election.id_election,inscriptions_bulk.date_election,db)

            if existing:
                logger.warning(f"Inscription existante pour candidat {candidat.nom_candidat}, ignorée")
                continue  # Ignorer ce candidat et continuer

            # Créer l'inscription
            db_inscription = InscriptionElection(
                id_election=election.id_election,
                id_candidat=candidat.id_candidat,
                date_election=inscriptions_bulk.date_election
            )

            db.add(db_inscription)
            created_inscriptions.append(db_inscription)

        # Si aucune inscription n'a pu être créée
        if not created_inscriptions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune inscription n'a pu être créée. Vérifiez les candidats et les inscriptions existantes."
            )

        db.commit()

        # Rafraîchir toutes les inscriptions créées
        for inscription in created_inscriptions:
            db.refresh(inscription)

        logger.info(f"{len(created_inscriptions)} inscriptions créées en masse pour l'élection {election.id_election}")
        return created_inscriptions

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création en masse: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création en masse: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_all_inscriptions(db: Session) -> List[InscriptionElectionReponse]:
    """
    Récupère toutes les inscriptions d'élection.

    Args:
        db: Session de base de données

    Returns:
        List[InscriptionElectionReponse]: Liste des inscriptions

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        inscriptions = db.query(InscriptionElection).all()

        result = []
        for inscription in inscriptions:
            inscription_response = InscriptionElectionReponse(
                id_election=inscription.id_election,
                id_candidat=inscription.id_candidat,
                date_election=inscription.date_election,
                created_at=inscription.created_at
            )
            result.append(inscription_response)

        logger.info(f"Récupération de {len(result)} inscriptions")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des inscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des inscriptions"
        )


def get_inscription_by_keys(
    id_election: int,
    id_candidat: int,
    date_election: date,
    db: Session
) -> Optional[InscriptionElection]:
    """
    Récupère une inscription par ses clés primaires.

    Args:
        id_election: ID de l'élection
        id_candidat: ID du candidat
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Optional[InscriptionElection]: L'inscription trouvée ou None
    """
    try:
        return db.query(InscriptionElection).filter(
            and_(
                InscriptionElection.id_election == id_election,
                InscriptionElection.id_candidat == id_candidat,
                InscriptionElection.date_election == date_election
            )
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de l'inscription: {e}")
        return None

def delete_inscription_election(
    id_election: int,
    nom_candidat: str,
    date_election: date,
    db: Session
) -> Dict[str, str]:
    """
    Supprime une inscription d'élection existante.

    Args:
        id_election: Identifiant de l'élection
        nom_candidat: Nom du candidat
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si l'inscription n'existe pas ou en cas d'erreur
    """
    try:
        # Rechercher l'ID de l'élection
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Rechercher l'ID du candidat
        candidat = db.query(Candidat).filter(
            Candidat.nom_candidat == nom_candidat.upper()
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat '{nom_candidat}' introuvable"
            )

        # Vérifier si l'inscription existe
        inscription = get_inscription_by_keys(election.id_election, candidat.id_candidat, date_election, db)
        if not inscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inscription introuvable pour ce candidat à cette élection et date"
            )

        # Supprimer l'inscription
        db.delete(inscription)
        db.commit()

        logger.info(f"Inscription supprimée avec succès pour élection {election.id_election}, candidat {candidat.id_candidat}")
        return {"message": f"Inscription supprimée avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression de l'inscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )