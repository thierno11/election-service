"""Contrôleur pour la gestion des centres de vote."""

from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.services.centre_votes_service import (
    create_centre,
    get_all_centres,
    get_centre_by_id,
    update_centre,
    delete_centre,
    get_centres_by_commune,
    get_all_centres_without_pagination
)
from app.schema.centre_votes_schema import CentreVotesSchema
from app.db.connexion import get_database


centre_vote_router = APIRouter(
    prefix="/elections/centres-votes",
    tags=["Centres de Vote"]
)


@centre_vote_router.post("/", status_code=status.HTTP_201_CREATED)
def creer_centre(request: CentreVotesSchema, db: Session = Depends(get_database)):
    """
    Crée un nouveau centre de vote.

    - **nom_centre**: Nom du centre de vote
    - **id_commune**: ID de la commune dans laquelle se trouve le centre
    """
    return create_centre(request, db)


@centre_vote_router.get("/")
def recuperer_centres(page:int=Query(1,ge=1),limit:int=Query(10,le=100,ge=10),db: Session = Depends(get_database)):
    """
    Récupère tous les centres de vote avec leurs bureaux.

    Returns:
        Liste des centres avec leurs informations
    """
    return get_all_centres(page,limit,db)

@centre_vote_router.get("/all")
def recuperer_centres_all(db: Session = Depends(get_database)):
    """
    Récupère tous les centres de vote avec leurs bureaux.

    Returns:
        Liste des centres avec leurs informations
    """
    return get_all_centres_without_pagination(db)

@centre_vote_router.get("/{id_centre}", status_code=status.HTTP_200_OK)
def recuperer_centre_par_id(id_centre: int, db: Session = Depends(get_database)):
    """
    Récupère un centre de vote par son ID.

    - **id_centre**: Identifiant unique du centre
    """
    return get_centre_by_id(id_centre, db)


@centre_vote_router.put("/{id_centre}", status_code=status.HTTP_200_OK)
def modifier_centre(
    id_centre: int,
    request: CentreVotesSchema,
    db: Session = Depends(get_database)
):
    """
    Met à jour un centre de vote.

    - **id_centre**: Identifiant unique du centre à modifier
    - **nom_centre**: Nouveau nom du centre
    - **id_commune**: Nouvelle commune
    """
    return update_centre(id_centre, request, db)


@centre_vote_router.delete("/{id_centre}", status_code=status.HTTP_200_OK)
def supprimer_centre(id_centre: int, db: Session = Depends(get_database)):
    """
    Supprime un centre de vote.

    - **id_centre**: Identifiant unique du centre à supprimer
    """
    return delete_centre(id_centre, db)



@centre_vote_router.get("/commune/{id_commune}", status_code=status.HTTP_200_OK)
def recuperer_centres_par_commune(id_commune: int, db: Session = Depends(get_database)):
    """
    Récupère tous les centres de vote d'une commune spécifique.

    - **id_commune**: Identifiant unique de la commune

    Returns:
        Liste des centres avec leurs informations:
        - id_centre: ID du centre
        - nom_centre: Nom du centre
        - nombre_bureaux: Nombre de bureaux dans ce centre

    Example de réponse:
    ```json
    [
        {
            "id_centre": 25,
            "nom_centre": "ÉCOLE PRIMAIRE CENTRALE",
            "nombre_bureaux": 5
        },
        {
            "id_centre": 26,
            "nom_centre": "LYCÉE KENNEDY",
            "nombre_bureaux": 8
        }
    ]
    ```
    """
    return get_centres_by_commune(id_commune, db)
