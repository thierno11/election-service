"""Contrôleur pour la gestion des résultats de vote."""

from typing import Dict, List
from datetime import date
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.connexion import get_database
from app.schema.resultat_vote_schema import (
    ResultatVoteSchema,
    ResultatVoteBulkSchema,
    ResultatVoteReponse,
    StatistiquesResultatListe
)
from app.services.resultat_vote_service import (
    create_resultat_vote,
    create_resultats_bulk,
    delete_resultat,
    get_all_resultats,
    get_resultats_by_bureau,
    get_statistiques_resultats_nationales,
    get_statistiques_resultats_region_specifique,
    get_statistiques_resultats_departement_specifique,
    get_statistiques_resultats_commune_specifique,
    get_statistiques_resultats_centre_specifique,
    get_statistiques_resultats_bureau_specifique,
    get_votes_candidat_par_region,
    get_votes_candidat_par_departement,
    get_votes_candidat_par_commune,
    get_votes_candidat_par_centre,
    get_votes_candidat_par_bureau
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
    "/",
    response_model=ResultatVoteReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un résultat de vote",
    description="Crée un nouveau résultat de vote pour une élection, bureau et candidat."
)
def creer_resultat(
    resultat: ResultatVoteSchema,
    db: Session = Depends(get_database)
) -> ResultatVoteReponse:
    """
    Crée un nouveau résultat de vote.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **nom_candidat**: Nom du candidat
    - **date_election**: Date de l'élection
    - **voix**: Nombre de voix

    Returns:
        ResultatVoteReponse: Le résultat créé
    """
    created_resultat = create_resultat_vote(resultat, db)

    return ResultatVoteReponse(
        id_election=created_resultat.id_election,
        id_bureau=created_resultat.id_bureau,
        id_candidat=created_resultat.id_candidat,
        date_election=created_resultat.date_election,
        voix=created_resultat.voix
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


@resultat_vote_router.get(
    "/",
    response_model=List[ResultatVoteReponse],
    summary="Lister tous les résultats de vote",
    description="Récupère la liste de tous les résultats de vote."
)
def recuperer_resultats(
    db: Session = Depends(get_database)
) -> List[ResultatVoteReponse]:
    """
    Récupère tous les résultats de vote.

    Returns:
        List[ResultatVoteReponse]: Liste des résultats
    """
    return get_all_resultats(db)


@resultat_vote_router.get(
    "/bureau/{id_bureau}",
    response_model=List[ResultatVoteReponse],
    summary="Récupérer les résultats par bureau",
    description="Récupère tous les résultats pour un bureau de vote donné."
)
def recuperer_resultats_par_bureau(
    id_bureau: int,
    db: Session = Depends(get_database)
) -> List[ResultatVoteReponse]:
    """
    Récupère tous les résultats pour un bureau de vote.

    - **id_bureau**: L'identifiant unique du bureau de vote

    Returns:
        List[ResultatVoteReponse]: Liste des résultats pour ce bureau
    """
    return get_resultats_by_bureau(id_bureau, db)


@resultat_vote_router.delete(
    "/{id_election}/{nom_centre}/{numero_bureau}/{nom_candidat}/{date_election}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer un résultat de vote",
    description="Supprime un résultat de vote existant."
)
def supprimer_resultat(
    id_election: int,
    nom_centre: str,
    numero_bureau: int,
    nom_candidat: str,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, str]:
    """
    Supprime un résultat de vote existant.

    - **id_election**: Identifiant de l'élection
    - **nom_centre**: Nom du centre de vote
    - **numero_bureau**: Numéro du bureau de vote
    - **nom_candidat**: Nom du candidat
    - **date_election**: La date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, str]: Message de confirmation de suppression
    """
    return delete_resultat(id_election, nom_centre, numero_bureau, nom_candidat, date_election, db)


@resultat_vote_router.get(
    "/statistiques/bureau/{id_bureau}/{id_election}/{date_election}",
    summary="Statistiques de résultats pour un bureau de vote spécifique",
    description="Récupère les statistiques de résultats pour un bureau de vote donné."
)
def statistiques_resultats_bureau_specifique(
    id_bureau: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
):
    """
    Récupère les statistiques de résultats pour un bureau de vote spécifique.

    - **id_bureau**: Identifiant unique du bureau de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatGlobal: Statistiques du bureau avec pourcentages par candidat

    Example de réponse:
    ```json
    {
        "total_voix_global": 850,
        "resultats_candidats": [
            {
                "nom_candidat": "Jean Dupont",
                "total_voix": 500,
                "pourcentage": 58.82
            },
            {
                "nom_candidat": "Marie Martin",
                "total_voix": 350,
                "pourcentage": 41.18
            }
        ]
    }
    ```
    """
    return get_statistiques_resultats_bureau_specifique(id_bureau, id_election, date_election, db)


@resultat_vote_router.get(
    "/statistiques/national/{id_election}/{date_election}",
    summary="Statistiques de résultats nationales",
    description="Récupère les statistiques de résultats agrégées au niveau national pour une élection et une date données."
)
def statistiques_resultats_nationales(
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de résultats au niveau national.

    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatListe: Statistiques nationales avec pourcentages par candidat
    """
    return get_statistiques_resultats_nationales(id_election, date_election, db)


@resultat_vote_router.get(
    "/statistiques/region/{id_region}/{id_election}/{date_election}",
    summary="Statistiques de résultats pour une région spécifique",
    description="Récupère les statistiques de résultats pour une région donnée."
)
def statistiques_resultats_region_specifique(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) :
    """
    Récupère les statistiques de résultats pour une région spécifique.

    - **id_region**: Identifiant unique de la région
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatListe: Statistiques de la région avec pourcentages par candidat
    """
    return get_statistiques_resultats_region_specifique(id_region, id_election, date_election, db)


@resultat_vote_router.get(
    "/statistiques/departement/{id_departement}/{id_election}/{date_election}",
    summary="Statistiques de résultats pour un département spécifique",
    description="Récupère les statistiques de résultats pour un département donné."
)
def statistiques_resultats_departement_specifique(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
):
    """
    Récupère les statistiques de résultats pour un département spécifique.

    - **id_departement**: Identifiant unique du département
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatGlobal: Statistiques du département avec pourcentages par candidat

    Example de réponse:
    ```json
    {
        "total_voix_global": 45000,
        "resultats_candidats": [
            {
                "nom_candidat": "Jean Dupont",
                "total_voix": 25000,
                "pourcentage": 55.56
            },
            {
                "nom_candidat": "Marie Martin",
                "total_voix": 20000,
                "pourcentage": 44.44
            }
        ]
    }
    ```
    """
    return get_statistiques_resultats_departement_specifique(id_departement, id_election, date_election, db)


@resultat_vote_router.get(
    "/statistiques/commune/{id_commune}/{id_election}/{date_election}",
    summary="Statistiques de résultats pour une commune spécifique",
    description="Récupère les statistiques de résultats pour une commune donnée."
)
def statistiques_resultats_commune_specifique(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
):
    """
    Récupère les statistiques de résultats pour une commune spécifique.

    - **id_commune**: Identifiant unique de la commune
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatGlobal: Statistiques de la commune avec pourcentages par candidat

    Example de réponse:
    ```json
    {
        "total_voix_global": 15000,
        "resultats_candidats": [
            {
                "nom_candidat": "Jean Dupont",
                "total_voix": 8500,
                "pourcentage": 56.67
            },
            {
                "nom_candidat": "Marie Martin",
                "total_voix": 6500,
                "pourcentage": 43.33
            }
        ]
    }
    ```
    """
    return get_statistiques_resultats_commune_specifique(id_commune, id_election, date_election, db)


@resultat_vote_router.get(
    "/statistiques/centre/{nom_centre}/{id_election}/{date_election}",
    summary="Statistiques de résultats pour un centre de vote spécifique",
    description="Récupère les statistiques de résultats pour un centre de vote donné."
)
def statistiques_resultats_centre_specifique(
    nom_centre: str,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
):
    """
    Récupère les statistiques de résultats pour un centre de vote spécifique.

    - **nom_centre**: Nom du centre de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        StatistiquesResultatGlobal: Statistiques du centre avec pourcentages par candidat

    Example de réponse:
    ```json
    {
        "total_voix_global": 3500,
        "resultats_candidats": [
            {
                "nom_candidat": "Jean Dupont",
                "total_voix": 2100,
                "pourcentage": 60.00
            },
            {
                "nom_candidat": "Marie Martin",
                "total_voix": 1400,
                "pourcentage": 40.00
            }
        ]
    }
    ```
    """
    return get_statistiques_resultats_centre_specifique(nom_centre, id_election, date_election, db)


@resultat_vote_router.get(
    "/votes-candidat-par-region/{id_candidat}/{id_election}/{date_election}",
    response_model=Dict[str, int],
    summary="Votes d'un candidat par région",
    description="Récupère le nombre de votes pour un candidat spécifique réparti par région."
)
def votes_candidat_par_region(
    id_candidat: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par région.

    - **id_candidat**: Identifiant unique du candidat
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des régions comme clés
                       et le nombre de votes comme valeurs

    Example de réponse:
    ```json
    {
        "Dakar": 15000,
        "Thiès": 8500,
        "Saint-Louis": 6200,
        "Kaolack": 7800
    }
    ```
    """
    return get_votes_candidat_par_region(id_candidat, id_election, date_election, db)


@resultat_vote_router.get(
    "/votes-candidat-par-departement/{id_candidat}/{id_region}/{id_election}/{date_election}",
    response_model=Dict[str, int],
    summary="Votes d'un candidat par département dans une région",
    description="Récupère le nombre de votes pour un candidat spécifique réparti par département dans une région donnée."
)
def votes_candidat_par_departement(
    id_candidat: int,
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par département dans une région.

    - **id_candidat**: Identifiant unique du candidat
    - **id_region**: Identifiant unique de la région
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des départements comme clés
                       et le nombre de votes comme valeurs

    Example de réponse:
    ```json
    {
        "Dakar": 12000,
        "Pikine": 8500,
        "Guédiawaye": 4200,
        "Rufisque": 3800
    }
    ```

    Note: Seuls les départements de la région spécifiée sont inclus dans les résultats.
    """
    return get_votes_candidat_par_departement(id_candidat, id_region, id_election, date_election, db)


@resultat_vote_router.get(
    "/votes-candidat-par-commune/{id_candidat}/{id_departement}/{id_election}/{date_election}",
    response_model=Dict[str, int],
    summary="Votes d'un candidat par commune dans un département",
    description="Récupère le nombre de votes pour un candidat spécifique réparti par commune dans un département donné."
)
def votes_candidat_par_commune(
    id_candidat: int,
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par commune dans un département.

    - **id_candidat**: Identifiant unique du candidat
    - **id_departement**: Identifiant unique du département
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des communes comme clés
                       et le nombre de votes comme valeurs

    Example de réponse:
    ```json
    {
        "Dakar-Plateau": 5000,
        "Médina": 3500,
        "Fass-Gueule-Tapée": 2800,
        "Sicap-Liberté": 4200
    }
    ```

    Note: Seules les communes du département spécifié sont incluses dans les résultats.
    """
    return get_votes_candidat_par_commune(id_candidat, id_departement, id_election, date_election, db)


@resultat_vote_router.get(
    "/votes-candidat-par-centre/{id_candidat}/{id_commune}/{id_election}/{date_election}",
    response_model=Dict[str, int],
    summary="Votes d'un candidat par centre dans une commune",
    description="Récupère le nombre de votes pour un candidat spécifique réparti par centre de vote dans une commune donnée."
)
def votes_candidat_par_centre(
    id_candidat: int,
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par centre dans une commune.

    - **id_candidat**: Identifiant unique du candidat
    - **id_commune**: Identifiant unique de la commune
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des centres comme clés
                       et le nombre de votes comme valeurs

    Example de réponse:
    ```json
    {
        "École Primaire Centrale": 2500,
        "Lycée Technique": 1800,
        "Collège Municipal": 2100,
        "Mairie Annexe": 1500
    }
    ```

    Note: Seuls les centres de la commune spécifiée sont inclus dans les résultats.
    """
    return get_votes_candidat_par_centre(id_candidat, id_commune, id_election, date_election, db)


@resultat_vote_router.get(
    "/votes-candidat-par-bureau/{id_candidat}/{nom_centre}/{id_election}/{date_election}",
    response_model=Dict[str, int],
    summary="Votes d'un candidat par bureau dans un centre",
    description="Récupère le nombre de votes pour un candidat spécifique réparti par bureau de vote dans un centre donné."
)
def votes_candidat_par_bureau(
    id_candidat: int,
    nom_centre: str,
    id_election: int,
    date_election: date,
    db: Session = Depends(get_database)
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par bureau dans un centre.

    - **id_candidat**: Identifiant unique du candidat
    - **nom_centre**: Nom du centre de vote
    - **id_election**: Identifiant de l'élection
    - **date_election**: Date de l'élection (format: YYYY-MM-DD)

    Returns:
        Dict[str, int]: Dictionnaire avec les numéros de bureau comme clés (format "Bureau X")
                       et le nombre de votes comme valeurs

    Example de réponse:
    ```json
    {
        "Bureau 1": 450,
        "Bureau 2": 520,
        "Bureau 3": 480,
        "Bureau 4": 510
    }
    ```

    Note: Seuls les bureaux du centre spécifié sont inclus dans les résultats.
    """
    return get_votes_candidat_par_bureau(id_candidat, nom_centre, id_election, date_election, db)
