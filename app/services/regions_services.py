"""Service pour la gestion des régions."""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.model.region_model import Region
from app.model.departement_model import Departement
from app.schema.region_schema import RegionSchema, RegionReponse

logger = logging.getLogger(__name__)


def create_region(region: RegionSchema, db: Session) -> Region:
    """
    Crée une nouvelle région.

    Args:
        region: Données de la région à créer
        db: Session de base de données

    Returns:
        Region: La région créée

    Raises:
        HTTPException: Si la région existe déjà ou en cas d'erreur
    """
    try:
        # Vérifier si la région existe déjà
        existing = db.query(Region).filter(Region.nom_region == region.nom_region).first()
        if existing:
            logger.warning(f"Tentative de création d'une région existante: {region.nom_region}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La région '{region.nom_region}' existe déjà"
            )

        # Validation du nom
        if not region.nom_region or len(region.nom_region.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom de la région doit contenir au moins 2 caractères"
            )

        # Création de l'objet SQLAlchemy
        db_region = Region(**region.model_dump())

        # Ajout à la session et commit
        db.add(db_region)
        db.commit()
        db.refresh(db_region)

        logger.info(f"Région créée avec succès: {db_region.nom_region} (ID: {db_region.id_region})")
        return db_region

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création de la région: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création de la région: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_all_regions(page,limit,db: Session) -> List[RegionReponse]:
    """
    Récupère toutes les régions avec le nombre de départements.

    Args:
        db: Session de base de données

    Returns:
        List[RegionReponse]: Liste des régions avec leurs statistiques

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        offset = (page -1) * limit
        result = db.query(Region).offset(offset).limit(limit).all()
        total = db.query(Region).count()
        # Conversion en objets RegionReponse
        print(result)
        regions = [
            RegionReponse(
                id_region=r.id_region,
                nom_region=r.nom_region,
                nombre_departement=len(r.departements),
                departements= r.departements
            )
            for r in result
        ]

        logger.info(f"Récupération de {len(regions)} régions")
        return {"data":regions,"total":total}

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des régions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des régions"
        )
    

def get_all_regions_witout_pagination(db: Session) -> List[RegionReponse]:
    """
    Récupère toutes les régions avec le nombre de départements.

    Args:
        db: Session de base de données

    Returns:
        List[RegionReponse]: Liste des régions avec leurs statistiques

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        result = db.query(Region).all()
        # Conversion en objets RegionReponse
        regions = [
            RegionReponse(
                id_region=r.id_region,
                nom_region=r.nom_region,
                nombre_departement=len(r.departements),
                departements= r.departements
            )
            for r in result
        ]

        logger.info(f"Récupération de {len(regions)} régions")
        return regions

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des régions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des régions"
        )
    



def get_region_by_id(region_id: int, db: Session) -> Region:
    """
    Récupère une région par son ID.

    Args:
        region_id: ID de la région
        db: Session de base de données

    Returns:
        Optional[Region]: La région trouvée ou None
    """
    try:
        return db.query(Region).filter(Region.id_region == region_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de la région {region_id}: {e}")
        return None


def update_region(region_id: int, region_request: RegionSchema, db: Session) -> Region:
    """
    Met à jour une région existante.

    Args:
        region_id: ID de la région à mettre à jour
        region_request: Nouvelles données de la région
        db: Session de base de données

    Returns:
        Region: La région mise à jour

    Raises:
        HTTPException: Si la région n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si la région existe
        region = get_region_by_id(region_id, db)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Région avec l'ID {region_id} introuvable"
            )

        # Validation du nouveau nom
        if not region_request.nom_region or len(region_request.nom_region.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom de la région doit contenir au moins 2 caractères"
            )

        # Vérifier si le nouveau nom existe déjà (uniquement si différent)
        if region_request.nom_region != region.nom_region:
            existing = db.query(Region).filter(
                Region.nom_region == region_request.nom_region,
                Region.id_region != region_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le nom '{region_request.nom_region}' est déjà utilisé"
                )

        # Mettre à jour les champs
        old_name = region.nom_region
        region.nom_region = region_request.nom_region.strip()

        db.commit()
        db.refresh(region)

        logger.info(f"Région mise à jour: {old_name} -> {region.nom_region} (ID: {region_id})")
        return region

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la mise à jour de la région {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la mise à jour de la région {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def delete_region(region_id: int, db: Session) -> Dict[str, str]:
    """
    Supprime une région existante.

    Args:
        region_id: ID de la région à supprimer
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si la région n'existe pas ou en cas d'erreur
    """
    try:
        # Vérifier si la région existe
        region = get_region_by_id(region_id, db)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Région avec l'ID {region_id} introuvable"
            )

        # Vérifier s'il y a des départements associés
        dept_count = db.query(func.count(Departement.id_departement)).filter(
            Departement.id_region == region_id
        ).scalar()

        if dept_count > 0:
            logger.warning(f"Tentative de suppression d'une région avec {dept_count} départements")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de supprimer la région. Elle contient {dept_count} département(s)"
            )

        # Supprimer la région
        region_name = region.nom_region
        db.delete(region)
        db.commit()

        logger.info(f"Région supprimée avec succès: {region_name} (ID: {region_id})")
        return {"message": f"Région '{region_name}' supprimée avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression de la région {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )



def get_departements_for_region(id_region,db:Session):
    departements = db.query(Departement).filter(Departement.id_region==id_region).all()
    return departements


# Alias pour compatibilité
get_all_region = get_all_regions
