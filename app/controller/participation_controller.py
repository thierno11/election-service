"""Contrôleur pour la gestion des participations."""

from typing import Dict, List
from datetime import date
import logging
from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.participation_schema import (
    ParticipationSchema,
    ParticipationReponse,

)
from app.services.participation_service import (
    create_participation,
    delete_participation,
    get_all_participations,
    update_participation,
    get_statistiques_nationales,
    get_statistiques_bureau_specifique,
    get_statistiques_centre_specifique,
    get_statistiques_commune_specifique,
    get_statistiques_departement_specifique,
    get_statistiques_region_specifique,
    get_statistiques_participation_repartition_regions,
    get_statistiques_participation_repartition_departements,
    get_statistiques_participation_repartition_communes,
    get_statistiques_participation_repartition_centres,
    get_statistiques_participation_repartition_bureaux,
    get_evolution_votants_temporelle,
    get_evolution_votants_temporelle_region,
    get_evolution_votants_temporelle_departement,
    get_evolution_votants_temporelle_commune,
    get_evolution_votants_temporelle_centre
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
    "/",
    response_model=List[ParticipationReponse],
    summary="Lister toutes les participations",
    description="Récupère la liste de toutes les participations."
)
def recuperer_participations(page:int = Query(1,ge=1),limit:int = Query(10,ge=10,le=100),
    db: Session = Depends(get_database)
) -> List[ParticipationReponse]:
    """
    Récupère toutes les participations.

    Returns:
        List[ParticipationReponse]: Liste des participations
    """
    return get_all_participations(page,limit,db)




@participation_router.put(
    "/{id_election}/{nom_centre}/{numero_bureau}/{date_election}",
    response_model=ParticipationReponse,
    summary="Mettre à jour une participation",
    description="Met à jour une participation existante."
)
def modifier_participation(
    id_election: int,
    nom_centre: str,
    numero_bureau: int,
    date_election: date,
    participation_request: ParticipationSchema,
    db: Session = Depends(get_database)
) -> ParticipationReponse:
    """
    Met à jour une participation existante.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **date_election**: La date de l'élection (format: YYYY-MM-DD)

    Returns:
        ParticipationReponse: La participation mise à jour
    """
    updated_participation = update_participation(
        id_election,
        nom_centre,
        numero_bureau,
        date_election,
        participation_request,
        db
    )

    return ParticipationReponse(
        id_election=updated_participation.id_election,
        id_bureau=updated_participation.id_bureau,
        nombre_electeur=updated_participation.nombre_electeur,
        nombre_votant=updated_participation.nombre_votant,
        nombre_votant_hors_bureau=updated_participation.nombre_votant_hors_bureau,
        nombre_bulletin_null=updated_participation.nombre_bulletin_null,
        nombre_suffrage=updated_participation.nombre_suffrage,
        date_election=updated_participation.date_election,
        created_at=updated_participation.created_at
    )


@participation_router.delete(
    "/{id_election}/{nom_centre}/{numero_bureau}/{date_election}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une participation",
    description="Supprime une participation existante."
)
def supprimer_participation(
    id_election: int,
    nom_centre: str,
    numero_bureau: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime une participation existante.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **date_election**: La date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_participation(id_election, nom_centre, numero_bureau, date_election, db)




@participation_router.get(
    "/statistiques/national/{id_election}/{date_election}",
    summary="Statistiques de participation nationales",
    description="Récupère les statistiques de participation agrégées au niveau national pour une élection et une date données."
)
def statistiques_nationales(
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation au niveau national.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques nationales avec taux de participation
    """
    return get_statistiques_nationales(id_election, date_election, db)


@participation_router.get(
    "/statistiques/bureau/{id_bureau}/{id_election}/{date_election}",
    summary="Statistiques de participation pour un bureau spécifique",
    description="Récupère les statistiques de participation pour un bureau de vote spécifique."
)
def statistiques_bureau_specifique(
    id_bureau: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation pour un bureau spécifique.

    - **id_bureau**: Identifiant unique du bureau de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques du bureau avec taux de participation
    """
    return get_statistiques_bureau_specifique(id_bureau, id_election, date_election, db)


@participation_router.get(
    "/statistiques/centre/{nom_centre}/{id_election}/{date_election}",
    summary="Statistiques de participation pour un centre spécifique",
    description="Récupère les statistiques de participation pour un centre de vote spécifique."
)
def statistiques_centre_specifique(
    nom_centre: str,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation pour un centre spécifique.

    - **nom_centre**: Nom du centre de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques du centre avec taux de participation
    """
    return get_statistiques_centre_specifique(nom_centre, id_election, date_election, db)


@participation_router.get(
    "/statistiques/commune/{id_commune}/{id_election}/{date_election}",
    summary="Statistiques de participation pour une commune spécifique",
    description="Récupère les statistiques de participation pour une commune spécifique."
)
def statistiques_commune_specifique(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation pour une commune spécifique.

    - **id_commune**: Identifiant unique de la commune
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques de la commune avec taux de participation
    """
    return get_statistiques_commune_specifique(id_commune, id_election, date_election, db)


@participation_router.get(
    "/statistiques/departement/{id_departement}/{id_election}/{date_election}",
    summary="Statistiques de participation pour un département spécifique",
    description="Récupère les statistiques de participation pour un département spécifique."
)
def statistiques_departement_specifique(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation pour un département spécifique.

    - **id_departement**: Identifiant unique du département
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques du département avec taux de participation
    """
    return get_statistiques_departement_specifique(id_departement, id_election, date_election, db)


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


@participation_router.get(
    "/statistiques/repartition-regions/{id_election}/{date_election}",
    summary="Statistiques de participation avec répartition par régions",
    description="Récupère les statistiques de participation réparties par région pour une élection et une date données."
)
def statistiques_participation_repartition_regions(
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation avec répartition par régions.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques de participation par région incluant :
        - Nombre d'électeurs, votants, bulletins nuls, suffrages par région
        - Taux de participation et taux de suffrages valides par région
        - Nombre de bureaux par région
    """
    return get_statistiques_participation_repartition_regions(id_election, date_election, db)


@participation_router.get(
    "/statistiques/repartition-departements/{id_region}/{id_election}/{date_election}",
    summary="Statistiques de participation avec répartition par départements d'une région",
    description="Récupère les statistiques de participation réparties par département pour une région donnée."
)
def statistiques_participation_repartition_departements(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation avec répartition par départements pour une région.

    - **id_region**: Identifiant unique de la région
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesParticipationListe: Statistiques de participation par département incluant :
        - Nombre d'électeurs, votants, bulletins nuls, suffrages par département
        - Taux de participation et taux de suffrages valides par département
        - Nombre de bureaux par département
    """
    return get_statistiques_participation_repartition_departements(id_region, id_election, date_election, db)


@participation_router.get(
    "/statistiques/repartition-communes/{id_departement}/{id_election}/{date_election}",
    summary="Statistiques de participation avec répartition par communes d'un département",
    description="Récupère les statistiques de participation réparties par commune pour un département donné."
)
def statistiques_participation_repartition_communes(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation avec répartition par communes pour un département.

    - **id_departement**: Identifiant unique du département
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict: Statistiques de participation par commune incluant :
        - Nombre d'électeurs, votants, bulletins nuls, suffrages par commune
        - Taux de participation et taux de suffrages valides par commune
        - Nombre de bureaux par commune
    """
    return get_statistiques_participation_repartition_communes(id_departement, id_election, date_election, db)


@participation_router.get(
    "/statistiques/repartition-centres/{id_commune}/{id_election}/{date_election}",
    summary="Statistiques de participation avec répartition par centres d'une commune",
    description="Récupère les statistiques de participation réparties par centre de vote pour une commune donnée."
)
def statistiques_participation_repartition_centres(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation avec répartition par centres pour une commune.

    - **id_commune**: Identifiant unique de la commune
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict: Statistiques de participation par centre incluant :
        - Nombre d'électeurs, votants, bulletins nuls, suffrages par centre
        - Taux de participation et taux de suffrages valides par centre
        - Nombre de bureaux par centre
    """
    return get_statistiques_participation_repartition_centres(id_commune, id_election, date_election, db)


@participation_router.get(
    "/statistiques/repartition-bureaux/{nom_centre}/{id_election}/{date_election}",
    summary="Statistiques de participation avec répartition par bureaux d'un centre",
    description="Récupère les statistiques de participation réparties par bureau de vote pour un centre donné."
)
def statistiques_participation_repartition_bureaux(
    nom_centre: str,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de participation avec répartition par bureaux pour un centre.

    - **nom_centre**: Nom du centre de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict: Statistiques de participation par bureau incluant :
        - Nombre d'électeurs, votants, bulletins nuls, suffrages par bureau
        - Taux de participation et taux de suffrages valides par bureau
    """
    return get_statistiques_participation_repartition_bureaux(nom_centre, id_election, date_election, db)


# @participation_router.get(
#     "/statistiques/evolution-temporelle/{type_election}/{date_election}",
#     response_model=EvolutionParticipationTemporelleListe,
#     summary="Évolution temporelle des participations par intervalles de 15 minutes",
#     description="Récupère l'évolution temporelle des participations par intervalles de 15 minutes pour analyser le rythme de saisie des données."
# )



@participation_router.get(
    "/statistiques/evolution-votants-temporelle/{id_election}/{date_election}",
    summary="Évolution temporelle des votants par intervalles paramétrables",
    description="Récupère l'évolution temporelle du nombre de votants par intervalles de temps paramétrables pour analyser le rythme de saisie des participations."
)
def evolution_votants_temporelle(
    id_election: int,
    date_election: date,
    interval_minutes: int = 15,
    db: Session = Depends(get_database)
):
    """
    Récupère l'évolution temporelle du nombre de votants par intervalles paramétrables.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)
    - **interval_minutes**: Intervalle en minutes (15, 30, 60, 120)

    Returns:
        Dict: Évolution temporelle incluant :
        - Nombre de votants ajoutés par intervalle
        - Cumul des votants au fil du temps
        - Métadonnées temporelles (nombre d'intervalles, durée totale)
    """
    return get_evolution_votants_temporelle(id_election, date_election, db, interval_minutes)


@participation_router.get(
    "/statistiques/evolution-votants-temporelle-region/{id_region}/{id_election}/{date_election}",
    summary="Évolution temporelle des votants par région",
    description="Récupère l'évolution temporelle du nombre de votants par intervalles de temps paramétrables pour une région spécifique."
)
def evolution_votants_temporelle_region(
    id_region: int,
    id_election: int,
    date_election: date,
    interval_minutes: int = 15,
    db: Session = Depends(get_database)
):
    """
    Récupère l'évolution temporelle du nombre de votants par intervalles paramétrables pour une région.

    - **id_region**: Identifiant unique de la région
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)
    - **interval_minutes**: Intervalle en minutes (15, 30, 60, 120)

    Returns:
        Dict: Évolution temporelle pour la région incluant :
        - Informations de la région (ID, nom)
        - Nombre de votants ajoutés par intervalle dans cette région
        - Cumul des votants au fil du temps pour cette région
        - Métadonnées temporelles (nombre d'intervalles, durée totale)

    Example de réponse:
    ```json
    {
        "id_region": 1,
        "nom_region": "Dakar",
        "id_election": 1,
        "date_election": "2024-02-25",
        "interval_minutes": 15,
        "total_votants": 25000,
        "nombre_intervalles": 32,
        "evolution": [
            {
                "intervalle": "2024-02-25T08:00:00",
                "nouveaux_votants": 1500,
                "cumul_votants": 1500
            }
        ]
    }
    ```
    """
    return get_evolution_votants_temporelle_region(id_region, id_election, date_election, db, interval_minutes)


@participation_router.get(
    "/statistiques/evolution-votants-temporelle-departement/{id_departement}/{id_election}/{date_election}",
    summary="Évolution temporelle des votants par département",
    description="Récupère l'évolution temporelle du nombre de votants par intervalles de temps paramétrables pour un département spécifique."
)
def evolution_votants_temporelle_departement(
    id_departement: int,
    id_election: int,
    date_election: date,
    interval_minutes: int = 15,
    db: Session = Depends(get_database)
):
    """
    Récupère l'évolution temporelle du nombre de votants par intervalles paramétrables pour un département.

    - **id_departement**: Identifiant unique du département
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)
    - **interval_minutes**: Intervalle en minutes (15, 30, 60, 120)

    Returns:
        Dict: Évolution temporelle pour le département incluant :
        - Informations du département (ID, nom)
        - Nombre de votants ajoutés par intervalle dans ce département
        - Cumul des votants au fil du temps pour ce département
        - Métadonnées temporelles (nombre d'intervalles, durée totale)
    """
    return get_evolution_votants_temporelle_departement(id_departement, id_election, date_election, db, interval_minutes)


@participation_router.get(
    "/statistiques/evolution-votants-temporelle-commune/{id_commune}/{id_election}/{date_election}",
    summary="Évolution temporelle des votants par commune",
    description="Récupère l'évolution temporelle du nombre de votants par intervalles de temps paramétrables pour une commune spécifique."
)
def evolution_votants_temporelle_commune(
    id_commune: int,
    id_election: int,
    date_election: date,
    interval_minutes: int = 15,
    db: Session = Depends(get_database)
):
    """
    Récupère l'évolution temporelle du nombre de votants par intervalles paramétrables pour une commune.

    - **id_commune**: Identifiant unique de la commune
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)
    - **interval_minutes**: Intervalle en minutes (15, 30, 60, 120)

    Returns:
        Dict: Évolution temporelle pour la commune incluant :
        - Informations de la commune (ID, nom)
        - Nombre de votants ajoutés par intervalle dans cette commune
        - Cumul des votants au fil du temps pour cette commune
        - Métadonnées temporelles (nombre d'intervalles, durée totale)
    """
    return get_evolution_votants_temporelle_commune(id_commune, id_election, date_election, db, interval_minutes)


@participation_router.get(
    "/statistiques/evolution-votants-temporelle-centre/{nom_centre}/{id_election}/{date_election}",
    summary="Évolution temporelle des votants par centre de vote",
    description="Récupère l'évolution temporelle du nombre de votants par intervalles de temps paramétrables pour un centre de vote spécifique."
)
def evolution_votants_temporelle_centre(
    nom_centre: str,
    id_election: int,
    date_election: date,
    interval_minutes: int = 15,
    db: Session = Depends(get_database)
):
    """
    Récupère l'évolution temporelle du nombre de votants par intervalles paramétrables pour un centre de vote.

    - **nom_centre**: Nom du centre de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)
    - **interval_minutes**: Intervalle en minutes (15, 30, 60, 120)

    Returns:
        Dict: Évolution temporelle pour le centre incluant :
        - Informations du centre (nom)
        - Nombre de votants ajoutés par intervalle dans ce centre
        - Cumul des votants au fil du temps pour ce centre
        - Métadonnées temporelles (nombre d'intervalles, durée totale)

    Example de réponse:
    ```json
    {
        "nom_centre": "École Primaire Central",
        "id_election": 1,
        "date_election": "2024-02-25",
        "interval_minutes": 15,
        "total_votants": 2500,
        "nombre_intervalles": 28,
        "evolution": [
            {
                "intervalle": "2024-02-25T08:00:00",
                "nouveaux_votants": 150,
                "cumul_votants": 150
            }
        ]
    }
    ```
    """
    return get_evolution_votants_temporelle_centre(nom_centre, id_election, date_election, db, interval_minutes)