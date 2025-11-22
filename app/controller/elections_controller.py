"""Contrôleur pour la gestion des élections."""

from typing import Dict, List
from datetime import date
import logging
from fastapi import APIRouter, Depends, status, HTTPException,Query
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.election_schema import ElectionSchema, ElectionReponse
from app.services.elections_service import (
    create_election,
    delete_election,
    get_all_elections,
    update_election,
    get_election_by_id,
    get_dates_election
)

logger = logging.getLogger(__name__)

elections_router = APIRouter(
    prefix="/elections",
    tags=["Élections"],
    responses={
        404: {"description": "Élection non trouvée"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"}
    }
)


@elections_router.post(
    "/",
    response_model=ElectionReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle élection",
    description="Crée une nouvelle élection."
)
def creer_election(
    election: ElectionSchema,
    db: Session = Depends(get_database)
) -> ElectionReponse:
    """
    Crée une nouvelle élection.

    - **type_election**: Type d'élection

    Returns:
        ElectionReponse: L'élection créée
    """
    created_election = create_election(election, db)

    return ElectionReponse(
        id_election=created_election.id_election,
        type_election=created_election.type_election
    )


@elections_router.get(
    "/",
    response_model=List[ElectionReponse],
    summary="Lister toutes les élections",
    description="Récupère la liste de toutes les élections."
)
def recuperer_elections(
    db: Session = Depends(get_database)
) -> List[ElectionReponse]:
    """
    Récupère toutes les élections.

    Returns:
        List[ElectionReponse]: Liste des élections
    """
    return get_all_elections(db)


@elections_router.get(
    "/{election_id}",
    response_model=ElectionReponse,
    summary="Récupérer une élection par ID",
    description="Récupère une élection par son ID."
)
def recuperer_election_par_id(
    election_id: int,
    db: Session = Depends(get_database)
) -> ElectionReponse:
    """
    Récupère une élection par son ID.

    - **election_id**: L'identifiant unique de l'élection

    Returns:
        ElectionReponse: L'élection trouvée
    """
    election = get_election_by_id(election_id, db)
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Élection avec l'ID {election_id} introuvable"
        )

    return ElectionReponse(
        id_election=election.id_election,
        type_election=election.type_election
    )


@elections_router.put(
    "/{election_id}",
    response_model=ElectionReponse,
    summary="Mettre à jour une élection",
    description="Met à jour une élection existante."
)
def modifier_election(
    election_id: int,
    election_request: ElectionSchema,
    db: Session = Depends(get_database)
) -> ElectionReponse:
    """
    Met à jour une élection existante.

    - **election_id**: L'identifiant unique de l'élection à modifier
    - **type_election**: Le nouveau type d'élection

    Returns:
        ElectionReponse: L'élection mise à jour
    """
    updated_election = update_election(election_id, election_request, db)

    return ElectionReponse(
        id_election=updated_election.id_election,
        type_election=updated_election.type_election
    )


@elections_router.delete(
    "/{election_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une élection",
    description="Supprime une élection existante."
)
def supprimer_election(
    election_id: int,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime une élection existante.

    - **election_id**: L'identifiant unique de l'élection à supprimer

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_election(election_id, db)


@elections_router.get(
    "/{election_id}/dates",
    response_model=List[date],
    summary="Récupérer les dates d'une élection",
    description="Récupère toutes les dates distinctes pour une élection spécifique."
)
def recuperer_dates_election(
    election_id: int,
    db: Session = Depends(get_database)
) -> List[date]:
    """
    Récupère les dates distinctes d'une élection spécifique.

    - **election_id**: L'identifiant unique de l'élection

    Returns:
        List[date]: Liste des dates distinctes pour cette élection, triées par ordre chronologique

    Example de réponse:
    ```json
    [
        "2024-02-25",
        "2024-03-15",
        "2024-04-10"
    ]
    ```
    """
    return get_dates_election(election_id, db)