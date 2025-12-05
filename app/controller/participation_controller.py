"""Contrôleur pour la gestion des participations."""

from datetime import date
import logging
from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.participation_schema import (
    ParticipationSchema,
    ParticipationReponse

)
from app.services.participation_service import (
    create_participation,
    get_statistiques_region_specifique,
)

logger = logging.getLogger(__name__)

participation_router = APIRouter(
    prefix="/elections/participations",
    tags=["Participations"],
    responses={
        404: {"description": "Participation non trouvée"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur interne du serveur"},
        409: {"description": "Participation existe deja"}
    }
)


@participation_router.post(
    "/",
    response_model=ParticipationReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle participation",
    description="Crée une nouvelle participation pour une élection et un bureau."
)
def creer_participation(
    participation: ParticipationSchema,
    db: Session = Depends(get_database)
) -> ParticipationReponse:
    """
    Crée une nouvelle participation.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **nombre_electeur**: Nombre d'électeurs inscrits
    - **nombre_votant**: Nombre de votants
    - **nombre_votant_hors_bureau**: Nombre de votants hors bureau
    - **nombre_bulletin_null**: Nombre de bulletins nuls
    - **nombre_suffrage**: Nombre de suffrages exprimés
    - **date_election**: Date de l'élection

    Returns:
        ParticipationReponse: La participation créée
    """
    created_participation = create_participation(participation, db)

    return ParticipationReponse(
        id_election=created_participation.id_election,
        id_bureau=created_participation.id_bureau,
        nombre_electeur=created_participation.nombre_electeur,
        nombre_votant=created_participation.nombre_votant,
        nombre_votant_hors_bureau=created_participation.nombre_votant_hors_bureau,
        nombre_bulletin_null=created_participation.nombre_bulletin_null,
        nombre_suffrage=created_participation.nombre_suffrage,
        date_election=created_participation.date_election,
        created_at=created_participation.created_at
    )



@participation_router.get(
    "/statistiques/region/{id_region}/{id_election}/{date_election}",
    summary="Statistiques de participation pour une région spécifique",
    description="Récupère les statistiques de participation pour une région spécifique."
)

def statistiques_region_specifique(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation pour une région spécifique.

    - **id_region**: Identifiant unique de la région
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques de la région avec taux de participation
    """
    return get_statistiques_region_specifique(id_region, id_election, date_election, db)
