"""Contrôleur pour la gestion des régions."""

from typing import Dict, List
from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.region_schema import RegionSchema, RegionReponse
from app.services.regions_services import (
    create_region,
    delete_region,
    get_all_regions,
    update_region,
    get_all_regions_witout_pagination,
    get_departements_for_region
    
)

regions_router = APIRouter(
    prefix="/elections/regions",
    tags=["Régions"],
    responses={
        404: {"description": "Région non trouvée"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"}
    }
)


@regions_router.post(
    "/",
    response_model=RegionReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle région",
    description="Crée une nouvelle région administrative avec validation des données."
)
def creer_region(
    region: RegionSchema,
    db: Session = Depends(get_database)
) -> RegionReponse:
    """
    Crée une nouvelle région.

    - **nom_region**: Le nom de la région (minimum 2 caractères, sera mis en majuscules)

    Returns:
        RegionReponse: La région créée avec son ID et le nombre de départements (0)
    """
    return create_region(region, db)


@regions_router.get(
    "/",
    summary="Lister toutes les régions",
    description="Récupère la liste de toutes les régions avec le nombre de départements pour chacune."
)
def recuperer_region(page:int = Query(1,ge=1),limit:int = Query(5,ge=5,le=100),
    db: Session = Depends(get_database)
):
    """
    Récupère toutes les régions.

    Returns:
        List[RegionReponse]: Liste des régions avec leurs statistiques
    """
    return get_all_regions(page,limit,db)

@regions_router.get(
    "/all",
    summary="Lister toutes les régions",
    description="Récupère la liste de toutes les régions avec le nombre de départements pour chacune."
)
def recuperer_regions(
    db: Session = Depends(get_database)
) :
    """
    Récupère toutes les régions.

    Returns:
        List[RegionReponse]: Liste des régions avec leurs statistiques
    """
    return get_all_regions_witout_pagination(db)

@regions_router.get(
    "/{region_id}",
    response_model=RegionReponse,
    summary="Récupérer une région par ID",
    description="Récupère les détails d'une région spécifique par son identifiant."
)
def recuperer_region_par_id(
    region_id: int,
    db: Session = Depends(get_database)
) -> RegionReponse:
    """
    Récupère une région par son ID.

    - **region_id**: L'identifiant unique de la région

    Returns:
        RegionReponse: Les détails de la région avec le nombre de départements
    """
    from services.regions_services import get_region_by_id
    from fastapi import HTTPException

    region = get_region_by_id(region_id, db)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Région avec l'ID {region_id} introuvable"
        )

    # Compter les départements
    from sqlalchemy import func
    from model.departement_model import Departement

    nombre_departements = db.query(func.count(Departement.id_departement)).filter(
        Departement.id_region == region_id
    ).scalar() or 0

    return RegionReponse(
        id_region=region.id_region,
        nom_region=region.nom_region,
        nombre_departement=nombre_departements
    )


@regions_router.put(
    "/{region_id}",
    response_model=RegionReponse,
    summary="Mettre à jour une région",
    description="Met à jour les informations d'une région existante."
)
def modifier_region(
    region_id: int,
    region_request: RegionSchema,
    db: Session = Depends(get_database)
) -> RegionReponse:
    """
    Met à jour une région existante.

    - **region_id**: L'identifiant unique de la région à modifier
    - **nom_region**: Le nouveau nom de la région

    Returns:
        RegionReponse: La région mise à jour avec ses statistiques
    """
    updated_region = update_region(region_id, region_request, db)

    # Compter les départements pour la réponse
    from sqlalchemy import func
    from model.departement_model import Departement

    nombre_departements = db.query(func.count(Departement.id_departement)).filter(
        Departement.id_region == region_id
    ).scalar() or 0

    return RegionReponse(
        id_region=updated_region.id_region,
        nom_region=updated_region.nom_region,
        nombre_departement=nombre_departements
    )


@regions_router.delete(
    "/{region_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une région",
    description="Supprime une région existante. La région ne doit contenir aucun département."
)
def supprimer_region(
    region_id: int,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime une région existante.

    - **region_id**: L'identifiant unique de la région à supprimer

    Note: La région ne peut être supprimée que si elle ne contient aucun département.

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_region(region_id, db)


@regions_router.get("/{id_region}/departements")
def get_departements_by_region(id_region:int,db:Session=Depends(get_database)):
    return get_departements_for_region(id_region,db)