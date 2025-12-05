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
    create_inscriptions_bulk,
    get_all_inscriptions,
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