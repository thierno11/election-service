"""Contrôleur pour la gestion des résultats de vote."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.resultat_vote_schema import (
    ResultatVoteBulkSchema,
    ResultatVoteReponse,
)
from app.services.resultat_vote_service import (
    create_resultats_bulk
)

logger = logging.getLogger(__name__)

resultat_vote_router = APIRouter(
    prefix="/elections/resultats-votes",
    tags=["Résultats de vote"],
    responses={
        404: {"description": "Résultat non trouvé"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"},
        409: {"description": "Resultat existe deja"}
    }
)



@resultat_vote_router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Créer plusieurs résultats de vote",
    description="Crée plusieurs résultats de vote en une seule opération pour une élection et un bureau."
)
def creer_resultats_bulk(
    resultats_bulk: ResultatVoteBulkSchema,
    db: Session = Depends(get_database)
):
    """
    Crée plusieurs résultats de vote en masse.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **date_election**: Date de l'élection
    - **resultats**: Liste des résultats [{nom_candidat, voix}, ...]

    Returns:
        List[ResultatVoteReponse]: Liste des résultats créés
    """
    created_resultats = create_resultats_bulk(resultats_bulk, db)

    result = []
    for resultat in created_resultats:
        result.append(
            ResultatVoteReponse(
                id_election=resultat.id_election,
                id_bureau=resultat.id_bureau,
                id_candidat=resultat.id_candidat,
                date_election=resultat.date_election,
                voix=resultat.voix
            )
        )

    return result
