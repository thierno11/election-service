"""Contrôleur pour la gestion des bureaux de vote."""

from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.services.bureau_vote_service import (
    create_bureau,
    get_all_bureaux,
    get_bureau_by_id,
    update_bureau,
    delete_bureau,
    get_bureaux_by_centre
)
from app.schema.bureau_vote_schema import BureauVoteSchema, BureauVoteReponse
from app.db.connexion import get_database


bureau_vote_router = APIRouter(
    prefix="/elections/bureaux-votes",
    tags=["Bureaux de Vote"]
)


@bureau_vote_router.post("/", status_code=status.HTTP_201_CREATED)
def creer_bureau(request: BureauVoteSchema, db: Session = Depends(get_database)):
    """
    Crée un nouveau bureau de vote.

    - **numero_bureau**: Numéro du bureau
    - **implantation**: Lieu d'implantation du bureau
    - **id_centre**: ID du centre de vote auquel le bureau appartient
    """
    return create_bureau(request, db)


@bureau_vote_router.get("/")
def recuperer_bureaux(page: int = Query(1, ge=1),
      limit: int = Query(10, ge=1, le=100),db: Session = Depends(get_database)):
    """
    Récupère tous les bureaux de vote avec leurs centres.

    Returns:
        Dict contenant:
        - data: Liste des bureaux
        - total: Nombre total de bureaux
    """
    return get_all_bureaux(page,limit,db)


@bureau_vote_router.get("/{id_bureau}", status_code=status.HTTP_200_OK)
def recuperer_bureau_par_id(id_bureau: int, db: Session = Depends(get_database)):
    """
    Récupère un bureau de vote par son ID.

    - **id_bureau**: Identifiant unique du bureau
    """
    return get_bureau_by_id(id_bureau, db)


@bureau_vote_router.put("/{id_bureau}", status_code=status.HTTP_200_OK)
def modifier_bureau(
    id_bureau: int,
    request: BureauVoteSchema,
    db: Session = Depends(get_database)
):
    """
    Met à jour un bureau de vote.

    - **id_bureau**: Identifiant unique du bureau à modifier
    - **numero_bureau**: Nouveau numéro du bureau
    - **implantation**: Nouveau lieu d'implantation
    - **id_centre**: Nouveau centre de vote
    """
    return update_bureau(id_bureau, request, db)


@bureau_vote_router.delete("/{id_bureau}", status_code=status.HTTP_200_OK)
def supprimer_bureau(id_bureau: int, db: Session = Depends(get_database)):
    """
    Supprime un bureau de vote.

    - **id_bureau**: Identifiant unique du bureau à supprimer
    """
    return delete_bureau(id_bureau, db)


@bureau_vote_router.get("/centre/{id_centre}", status_code=status.HTTP_200_OK)
def recuperer_bureaux_par_centre(
    id_centre: int,
    db: Session = Depends(get_database)
):
    """
    Récupère tous les bureaux de vote d'un centre spécifique.

    - **id_centre**: Identifiant unique du centre de vote

    Returns:
        Liste des bureaux avec leurs informations:
        - id_bureau: ID du bureau
        - numero_bureau: Numéro du bureau
        - implantation: Lieu d'implantation
        - id_centre: ID du centre

    Example de réponse:
    ```json
    [
        {
            "id_bureau": 101,
            "numero_bureau": 1,
            "implantation": "Avenue Roume",
            "id_centre": 25
        },
        {
            "id_bureau": 102,
            "numero_bureau": 2,
            "implantation": "Avenue Roume",
            "id_centre": 25
        }
    ]
    ```
    """
    return get_bureaux_by_centre(id_centre, db)
