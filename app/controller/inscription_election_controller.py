"""Contrôleur pour la gestion des inscriptions d'élection."""

from typing import Dict, List
from datetime import date
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.inscription_election_schema import (
    InscriptionElectionSchema,
    InscriptionElectionReponse,
    InscriptionElectionAvecDetails,
    InscriptionElectionBulkSchema
)
from app.services.inscription_election_service import (
    create_inscription_election,
    create_inscriptions_bulk,
    get_all_inscriptions,
    get_all_inscriptions_avec_details,
    get_inscriptions_by_election,
    get_inscriptions_by_candidat,
    delete_inscription_election
)

logger = logging.getLogger(__name__)

inscription_election_router = APIRouter(
    prefix="/elections/inscriptions-elections",
    tags=["Inscriptions d'élection"],
    responses={
        404: {"description": "Inscription non trouvée"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"},
        409: {"description": "Inscription existe déjà"}
    }
)


@inscription_election_router.post(
    "/",
    response_model=InscriptionElectionReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle inscription d'élection",
    description="Inscrit un candidat à une élection pour une date donnée."
)
def creer_inscription(
    inscription: InscriptionElectionSchema,
    db: Session = Depends(get_database)
) -> InscriptionElectionReponse:
    """
    Crée une nouvelle inscription d'élection.

    - **id_election**: Identifiant de l'élection
    - **nom_candidat**: Nom du candidat
    - **date_election**: Date de l'élection

    Returns:
        InscriptionElectionReponse: L'inscription créée
    """
    created_inscription = create_inscription_election(inscription, db)

    return InscriptionElectionReponse(
        id_election=created_inscription.id_election,
        id_candidat=created_inscription.id_candidat,
        date_election=created_inscription.date_election,
        created_at=created_inscription.created_at
    )


@inscription_election_router.post(
    "/bulk",
    response_model=List[InscriptionElectionReponse],
    status_code=status.HTTP_201_CREATED,
    summary="Créer plusieurs inscriptions d'élection",
    description="Inscrit plusieurs candidats à une élection en une seule opération."
)
def creer_inscriptions_bulk(
    inscriptions_bulk: InscriptionElectionBulkSchema,
    db: Session = Depends(get_database)
) -> List[InscriptionElectionReponse]:
    """
    Crée plusieurs inscriptions d'élection en masse.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection
    - **candidats**: Liste des candidats à inscrire [{"nom_candidat": "nom"}, ...]

    **Comportement** :
    - Les candidats inexistants sont ignorés (pas d'erreur)
    - Les doublons dans la requête sont ignorés
    - Les inscriptions déjà existantes sont ignorées
    - Au moins une inscription doit être créée sinon erreur 400

    Returns:
        List[InscriptionElectionReponse]: Liste des inscriptions créées

    Example de requête:
    ```json
    {
        "id_election": 1,
        "date_election": "2024-02-25",
        "candidats": [
            {"nom_candidat": "Jean Dupont"},
            {"nom_candidat": "Marie Martin"},
            {"nom_candidat": "Pierre Durand"}
        ]
    }
    ```
    """
    created_inscriptions = create_inscriptions_bulk(inscriptions_bulk, db)

    result = []
    for inscription in created_inscriptions:
        result.append(
            InscriptionElectionReponse(
                id_election=inscription.id_election,
                id_candidat=inscription.id_candidat,
                date_election=inscription.date_election,
                created_at=inscription.created_at
            )
        )

    return result


@inscription_election_router.get(
    "/",
    response_model=List[InscriptionElectionReponse],
    summary="Lister toutes les inscriptions",
    description="Récupère la liste de toutes les inscriptions d'élection."
)
def recuperer_inscriptions(
    db: Session = Depends(get_database)
) -> List[InscriptionElectionReponse]:
    """
    Récupère toutes les inscriptions d'élection.

    Returns:
        List[InscriptionElectionReponse]: Liste des inscriptions
    """
    return get_all_inscriptions(db)


@inscription_election_router.get(
    "/avec-details",
    response_model=List[InscriptionElectionAvecDetails],
    summary="Lister toutes les inscriptions avec détails",
    description="Récupère la liste de toutes les inscriptions avec les noms des candidats et types d'élections."
)
def recuperer_inscriptions_avec_details(
    db: Session = Depends(get_database)
) -> List[InscriptionElectionAvecDetails]:
    """
    Récupère toutes les inscriptions d'élection avec les détails.

    Returns:
        List[InscriptionElectionAvecDetails]: Liste des inscriptions avec noms
    """
    return get_all_inscriptions_avec_details(db)


@inscription_election_router.get(
    "/election/{id_election}/{date_election}",
    response_model=List[InscriptionElectionAvecDetails],
    summary="Inscriptions pour une élection",
    description="Récupère toutes les inscriptions pour une élection et une date données."
)
def recuperer_inscriptions_par_election(
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> List[InscriptionElectionAvecDetails]:
    """
    Récupère toutes les inscriptions pour une élection donnée.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        List[InscriptionElectionAvecDetails]: Liste des candidats inscrits à cette élection
    """
    return get_inscriptions_by_election(id_election, date_election, db)


@inscription_election_router.get(
    "/candidat/{nom_candidat}",
    response_model=List[InscriptionElectionAvecDetails],
    summary="Inscriptions d'un candidat",
    description="Récupère toutes les inscriptions d'un candidat donné."
)
def recuperer_inscriptions_par_candidat(
    nom_candidat: str,
    db: Session = Depends(get_database)
) -> List[InscriptionElectionAvecDetails]:
    """
    Récupère toutes les inscriptions d'un candidat donné.

    - **nom_candidat**: Nom du candidat

    Returns:
        List[InscriptionElectionAvecDetails]: Liste des élections auxquelles ce candidat est inscrit
    """
    return get_inscriptions_by_candidat(nom_candidat, db)


@inscription_election_router.delete(
    "/{id_election}/{nom_candidat}/{date_election}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une inscription d'élection",
    description="Supprime une inscription d'élection existante."
)
def supprimer_inscription(
    id_election: int,
    nom_candidat: str,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime une inscription d'élection existante.

    - **id_election**: Identifiant de l'élection
    - **nom_candidat**: Nom du candidat
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_inscription_election(id_election, nom_candidat, date_election, db)