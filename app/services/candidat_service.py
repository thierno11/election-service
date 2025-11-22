"""Service pour la gestion des candidats."""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.model.candidat_model import Candidat
from app.schema.candidat_schema import CandidatSchema, CandidatReponse

logger = logging.getLogger(__name__)


def create_candidat(candidat: CandidatSchema, db: Session) -> Candidat:
    """
    Crée un nouveau candidat.

    Args:
        candidat: Données du candidat à créer
        db: Session de base de données

    Returns:
        Candidat: Le candidat créé

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier si un candidat avec le même nom existe déjà
        existing = db.query(Candidat).filter(
            Candidat.nom_candidat == candidat.nom_candidat
        ).first()

        if existing:
            logger.warning(f"Tentative de création d'un candidat existant: {candidat.nom_candidat}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le candidat '{candidat.nom_candidat}' existe déjà"
            )

        # Créer le candidat
        db_candidat = Candidat(**candidat.model_dump())

        db.add(db_candidat)
        db.commit()
        db.refresh(db_candidat)

        logger.info(f"Candidat créé avec succès: {db_candidat.nom_candidat} (ID: {db_candidat.id_candidat})")
        return db_candidat

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création du candidat: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création du candidat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_all_candidats(page,limit,db: Session) -> List[CandidatReponse]:
    """
    Récupère tous les candidats.

    Args:
        db: Session de base de données

    Returns:
        List[CandidatReponse]: Liste des candidats

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        offset = (page - 1) * limit
        candidats = db.query(Candidat).offset(offset).limit(limit).all()
        total = db.query(Candidat).count()
        # Conversion en objets CandidatReponse
        result = []
        for candidat in candidats:
            candidat_response = CandidatReponse(
                id_candidat=candidat.id_candidat,
                nom_candidat=candidat.nom_candidat
            )
            result.append(candidat_response)

        logger.info(f"Récupération de {len(result)} candidats")
        return {"data":result,"total":total}

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des candidats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des candidats"
        )


def get_all_candidats_without_pagination(db: Session) -> List[CandidatReponse]:
    """
    Récupère tous les candidats.

    Args:
        db: Session de base de données

    Returns:
        List[CandidatReponse]: Liste des candidats

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        candidats = db.query(Candidat).all()
        # Conversion en objets CandidatReponse
        result = []
        for candidat in candidats:
            candidat_response = CandidatReponse(
                id_candidat=candidat.id_candidat,
                nom_candidat=candidat.nom_candidat
            )
            result.append(candidat_response)

        logger.info(f"Récupération de {len(result)} candidats")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des candidats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des candidats"
        )





def get_candidat_by_id(candidat_id: int, db: Session) -> Optional[Candidat]:
    """
    Récupère un candidat par son ID.

    Args:
        candidat_id: ID du candidat
        db: Session de base de données

    Returns:
        Optional[Candidat]: Le candidat trouvé ou None
    """
    try:
        return db.query(Candidat).filter(Candidat.id_candidat == candidat_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération du candidat {candidat_id}: {e}")
        return None


def update_candidat(candidat_id: int, candidat_request: CandidatSchema, db: Session) -> Candidat:
    """
    Met à jour un candidat existant.

    Args:
        candidat_id: ID du candidat à mettre à jour
        candidat_request: Nouvelles données du candidat
        db: Session de base de données

    Returns:
        Candidat: Le candidat mis à jour

    Raises:
        HTTPException: Si le candidat n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si le candidat existe
        candidat = get_candidat_by_id(candidat_id, db)
        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {candidat_id} introuvable"
            )

        # Vérifier si le nouveau nom existe déjà (uniquement si différent)
        if candidat_request.nom_candidat != candidat.nom_candidat:
            existing = db.query(Candidat).filter(
                Candidat.nom_candidat == candidat_request.nom_candidat,
                Candidat.id_candidat != candidat_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le nom '{candidat_request.nom_candidat}' est déjà utilisé"
                )

        # Mettre à jour les champs
        for field, value in candidat_request.model_dump().items():
            setattr(candidat, field, value)

        db.commit()
        db.refresh(candidat)

        logger.info(f"Candidat mis à jour: {candidat.nom_candidat} (ID: {candidat_id})")
        return candidat

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la mise à jour du candidat {candidat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la mise à jour du candidat {candidat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def delete_candidat(candidat_id: int, db: Session) -> Dict[str, str]:

    """
    Supprime un candidat existant.

    Args:
        candidat_id: ID du candidat à supprimer
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si le candidat n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si le candidat existe
        candidat = get_candidat_by_id(candidat_id, db)
        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {candidat_id} introuvable"
            )

        # Supprimer le candidat
        candidat_name = candidat.nom_candidat
        db.delete(candidat)
        db.commit()

        logger.info(f"Candidat supprimé avec succès: {candidat_name} (ID: {candidat_id})")
        return {"message": f"Candidat '{candidat_name}' supprimé avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression du candidat {candidat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )
    

def get_allcandidats_ids(ids:List[int],db:Session):
    candidats = db.query(Candidat).filter(Candidat.id_candidat.in_(ids)).all()
    return candidats
