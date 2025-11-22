"""Contrôleur pour la gestion des candidats."""

from typing import Dict, List
import logging
from fastapi import APIRouter, Depends, status, HTTPException,Query
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.candidat_schema import CandidatSchema, CandidatReponse
from app.services.candidat_service import (
    create_candidat,
    delete_candidat,
    get_all_candidats,
    update_candidat,
    get_candidat_by_id,
    get_allcandidats_ids,
    get_all_candidats_without_pagination
)

logger = logging.getLogger(__name__)

candidat_router = APIRouter(
    prefix="/elections/candidats",
    tags=["Candidats"],
    responses={
        404: {"description": "Candidat non trouvé"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"}
    }
)


@candidat_router.post(
    "/",
    response_model=CandidatReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau candidat",
    description="Crée un nouveau candidat."
)
def creer_candidat(
    candidat: CandidatSchema,
    db: Session = Depends(get_database)
) -> CandidatReponse:
    """
    Crée un nouveau candidat.

    - **nom_candidat**: Nom du candidat

    Returns:
        CandidatReponse: Le candidat créé
    """
    created_candidat = create_candidat(candidat, db)

    return CandidatReponse(
        id_candidat=created_candidat.id_candidat,
        nom_candidat=created_candidat.nom_candidat
    )


@candidat_router.get(
    "/",
    summary="Lister tous les candidats",
    description="Récupère la liste de tous les candidats."
)
def recuperer_candidats(page:int = Query(1,ge=1),limit:int = Query(10,ge=10,le=100),
    db: Session = Depends(get_database)
) :
    """
    Récupère tous les candidats.

    Returns:
        List[CandidatReponse]: Liste des candidats
    """
    return get_all_candidats(page,limit,db)

@candidat_router.get(
    "/all",
    summary="Lister tous les candidats",
    description="Récupère la liste de tous les candidats."
)
def recuperer_all_candidats(
    db: Session = Depends(get_database)
) :
    """
    Récupère tous les candidats.

    Returns:
        List[CandidatReponse]: Liste des candidats
    """
    return get_all_candidats_without_pagination(db)


@candidat_router.get(
    "/{candidat_id}",
    response_model=CandidatReponse,
    summary="Récupérer un candidat par ID",
    description="Récupère un candidat par son ID."
)
def recuperer_candidat_par_id(
    candidat_id: int,
    db: Session = Depends(get_database)
) -> CandidatReponse:
    """
    Récupère un candidat par son ID.

    - **candidat_id**: L'identifiant unique du candidat

    Returns:
        CandidatReponse: Le candidat trouvé
    """
    candidat = get_candidat_by_id(candidat_id, db)
    if not candidat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidat avec l'ID {candidat_id} introuvable"
        )

    return CandidatReponse(
        id_candidat=candidat.id_candidat,
        nom_candidat=candidat.nom_candidat
    )


@candidat_router.put(
    "/{candidat_id}",
    response_model=CandidatReponse,
    summary="Mettre à jour un candidat",
    description="Met à jour un candidat existant."
)
def modifier_candidat(
    candidat_id: int,
    candidat_request: CandidatSchema,
    db: Session = Depends(get_database)
) -> CandidatReponse:
    """
    Met à jour un candidat existant.

    - **candidat_id**: L'identifiant unique du candidat à modifier
    - **nom_candidat**: Le nouveau nom du candidat

    Returns:
        CandidatReponse: Le candidat mis à jour
    """
    updated_candidat = update_candidat(candidat_id, candidat_request, db)

    return CandidatReponse(
        id_candidat=updated_candidat.id_candidat,
        nom_candidat=updated_candidat.nom_candidat
    )


@candidat_router.delete(
    "/{candidat_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer un candidat",
    description="Supprime un candidat existant."
)
def supprimer_candidat(
    candidat_id: int,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime un candidat existant.

    - **candidat_id**: L'identifiant unique du candidat à supprimer

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_candidat(candidat_id, db)

@candidat_router.post("/ids")
def get_candidadts_by_ids(ids:List[int],db:Session=Depends(get_database)):
    return get_allcandidats_ids(ids,db)
   