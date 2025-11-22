"""Service pour la gestion des résultats de vote."""

import logging
from typing import Dict, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from app.services.commune_service import  get_communes_by_nom_commune

from app.model.resultat_model import ResultatVote
from app.model.election_model import Election
from app.model.bureau_vote import BureauVote
from app.model.candidat_model import Candidat
from app.model.centres_votes_model import CentreVote
from app.model.commune_model import Commune
from app.model.departement_model import Departement
from app.model.region_model import Region
from app.schema.resultat_vote_schema import (
    ResultatVoteSchema,
    ResultatVoteBulkSchema,
    ResultatVoteReponse,
    StatistiquesResultat,
    StatistiquesResultatGlobal
)

logger = logging.getLogger(__name__)


def create_resultat_vote(resultat: ResultatVoteSchema, db: Session) -> ResultatVote:
    """
    Crée un nouveau résultat de vote.

    Args:
        resultat: Données du résultat à créer
        db: Session de base de données

    Returns:
        ResultatVote: Le résultat créé

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Rechercher l'ID de l'élection
        election = db.query(Election).filter(
            Election.id_election == resultat.id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {resultat.id_election} introuvable"
            )

        # Vérifier que le bureau existe
        bureau = db.query(BureauVote).filter(
            BureauVote.id_bureau == resultat.id_bureau
        ).first()

        if not bureau:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau avec l'ID {resultat.id_bureau} introuvable"
            )

        # Rechercher l'ID du candidat
        candidat = db.query(Candidat).filter(
            Candidat.nom_candidat == resultat.nom_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat '{resultat.nom_candidat}' introuvable"
            )

        # Vérifier si un résultat existe déjà pour cette combinaison
        existing = db.query(ResultatVote).filter(
            and_(
                ResultatVote.id_election == election.id_election,
                ResultatVote.id_bureau == resultat.id_bureau,
                ResultatVote.id_candidat == candidat.id_candidat,
                ResultatVote.date_election == resultat.date_election
            )
        ).first()

        if existing:
            logger.warning(f"Tentative de création d'un résultat existant")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un résultat existe déjà pour cette élection, bureau, candidat et date"
            )

        # Créer le résultat avec les IDs trouvés
        db_resultat = ResultatVote(
            id_election=election.id_election,
            id_bureau=resultat.id_bureau,
            id_candidat=candidat.id_candidat,
            date_election=resultat.date_election,
            voix=resultat.voix
        )

        db.add(db_resultat)
        db.commit()
        db.refresh(db_resultat)

        logger.info(f"Résultat créé avec succès pour élection {db_resultat.id_election}, bureau {db_resultat.id_bureau}, candidat {db_resultat.id_candidat}")
        return db_resultat

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création du résultat: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création du résultat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def create_resultats_bulk(resultats_bulk: ResultatVoteBulkSchema, db: Session) -> List[ResultatVote]:
    """
    Crée plusieurs résultats de vote en une seule opération.

    Args:
        resultats_bulk: Données des résultats à créer en masse
        db: Session de base de données

    Returns:
        List[ResultatVote]: Liste des résultats créés

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Rechercher l'élection par son type
        election = db.query(Election).filter(
            Election.type_election == resultats_bulk.type_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection de type '{resultats_bulk.type_election}' introuvable"
            )
        commune = get_communes_by_nom_commune(resultats_bulk.commune,db)
        print(commune)
        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune '{resultats_bulk.commune}' introuvable")
        centre_communes = commune.centres_vote

        # Recherche avec correspondance partielle (insensible à la casse)
        centre_search = resultats_bulk.centre.upper()
        centre = next((x for x in centre_communes if centre_search in x.nom_centre.upper()), None)

        print(centre)
        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre contenant '{resultats_bulk.centre}' introuvable")

        new_centre = db.query(CentreVote).filter(CentreVote.id_centre == centre.id_centre).first()

        bureau_vote = next((x for x in new_centre.bureaux_vote if x.numero_bureau == resultats_bulk.bureau), None)

        if not bureau_vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau numéro '{resultats_bulk.bureau}' introuvable dans le centre '{resultats_bulk.centre}'")
        # # Vérifier que le bureau existe
        # bureau = db.query(BureauVote).filter(
        #     BureauVote.id_bureau == resultats_bulk.id_bureau
        # ).first()

        # if not bureau:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Bureau avec l'ID {resultats_bulk.id_bureau} introuvable"
        #     )

        created_resultats = []

        for item in resultats_bulk.resultats:
            # Rechercher l'ID du candidat
            candidat = db.query(Candidat).filter(
                Candidat.nom_candidat == item.nom_candidat
            ).first()

            if not candidat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidat '{item.nom_candidat}' introuvable"
                )

            # Vérifier si un résultat existe déjà
            existing = db.query(ResultatVote).filter(
                and_(
                    ResultatVote.id_election == election.id_election,
                    ResultatVote.id_bureau == bureau_vote.id_bureau,
                    ResultatVote.id_candidat == candidat.id_candidat,
                    ResultatVote.date_election == resultats_bulk.date_election
                )
            ).first()

            if existing:
                logger.warning(f"Résultat existant pour candidat {candidat.nom_candidat}, on passe")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Le bureau a deja ete enregistre"
                )

            # Créer le résultat
            db_resultat = ResultatVote(
                id_election=election.id_election,
                id_bureau=bureau_vote.id_bureau,
                id_candidat=candidat.id_candidat,
                date_election=resultats_bulk.date_election,
                voix=item.voix
            )

            db.add(db_resultat)
            created_resultats.append(db_resultat)

        db.commit()

        # Rafraîchir tous les résultats créés
        for resultat in created_resultats:
            db.refresh(resultat)

        logger.info(f"{len(created_resultats)} résultats créés en masse")
        return created_resultats

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité lors de la création en masse: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur de contrainte de base de données"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la création en masse: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def get_all_resultats(db: Session) -> List[ResultatVoteReponse]:
    """
    Récupère tous les résultats de vote.

    Args:
        db: Session de base de données

    Returns:
        List[ResultatVoteReponse]: Liste des résultats

    Raises:
        HTTPException: En cas d'erreur de base de données
    """
    try:
        resultats = db.query(ResultatVote).all()

        result = []
        for resultat in resultats:
            resultat_response = ResultatVoteReponse(
                id_election=resultat.id_election,
                id_bureau=resultat.id_bureau,
                id_candidat=resultat.id_candidat,
                date_election=resultat.date_election,
                voix=resultat.voix
            )
            result.append(resultat_response)

        logger.info(f"Récupération de {len(result)} résultats")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des résultats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des résultats"
        )



def get_resultats_by_bureau(id_bureau: int, db: Session) -> List[ResultatVoteReponse]:
    """
    Récupère tous les résultats pour un bureau.

    Args:
        id_bureau: ID du bureau
        db: Session de base de données

    Returns:
        List[ResultatVoteReponse]: Liste des résultats
    """
    try:
        resultats = db.query(ResultatVote).filter(
            ResultatVote.id_bureau == id_bureau
        ).all()

        result = []
        for resultat in resultats:
            resultat_response = ResultatVoteReponse(
                id_election=resultat.id_election,
                id_bureau=resultat.id_bureau,
                id_candidat=resultat.id_candidat,
                date_election=resultat.date_election,
                voix=resultat.voix
            )
            result.append(resultat_response)

        return result

    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des résultats pour le bureau {id_bureau}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des résultats"
        )


def delete_resultat(
    id_election: int,
    id_bureau: int,
    nom_candidat: str,
    date_election: date,
    db: Session
) -> Dict[str, str]:
    """
    Supprime un résultat de vote.

    Args:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau de vote
        nom_candidat: Nom du candidat
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, str]: Message de confirmation

    Raises:
        HTTPException: Si le résultat n'existe pas ou en cas d'erreur
    """
    try:
        # Rechercher les IDs
        election = db.query(Election).filter(Election.id_election == id_election).first()
        if not election:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Élection avec l'ID {id_election} introuvable")

        bureau = db.query(BureauVote).filter(BureauVote.id_bureau == id_bureau).first()
        if not bureau:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bureau avec l'ID {id_bureau} introuvable")

        candidat = db.query(Candidat).filter(Candidat.nom_candidat == nom_candidat.upper()).first()
        if not candidat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidat '{nom_candidat}' introuvable")

        # Rechercher et supprimer le résultat
        resultat = db.query(ResultatVote).filter(
            and_(
                ResultatVote.id_election == election.id_election,
                ResultatVote.id_bureau == id_bureau,
                ResultatVote.id_candidat == candidat.id_candidat,
                ResultatVote.date_election == date_election
            )
        ).first()

        if not resultat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Résultat introuvable")

        db.delete(resultat)
        db.commit()

        logger.info(f"Résultat supprimé avec succès")
        return {"message": "Résultat supprimé avec succès"}

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur de base de données lors de la suppression: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur"
        )


def _calculer_pourcentage(voix_candidat: int, total_voix: int) -> float:
    """Calcule le pourcentage de voix d'un candidat."""
    if total_voix == 0:
        return 0.0
    return round((voix_candidat / total_voix) * 100, 2)


def get_statistiques_resultats_nationales(
    id_election: int,
    date_election: date,
    db: Session
) :
    """
    Récupère les statistiques de résultats nationales.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        query = db.query(
            Candidat.nom_candidat,
            func.sum(ResultatVote.voix).label('total_voix'),
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Candidat.nom_candidat).all()

        # Calculer le total national
        total_voix_national = sum(row.total_voix or 0 for row in query)

        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.total_voix or 0,
                pourcentage=_calculer_pourcentage(row.total_voix or 0, total_voix_national),
            )
            resultats_candidats.append(stat_candidat)

        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_national,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats nationales: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_resultats_region_specifique(
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session
) :
    """
    Récupère les statistiques de résultats pour une région spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la région existe
        region = db.query(Region).filter(
            Region.id_region == id_region
        ).first()

        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Région avec l'ID {id_region} introuvable"
            )

        # Requête pour récupérer les statistiques de résultats pour cette région
        query = db.query(
            Candidat.nom_candidat,
            func.sum(ResultatVote.voix).label('total_voix'),
        ).join(
            BureauVote, ResultatVote.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).join(
            Commune, CentreVote.id_commune == Commune.id_commune
        ).join(
            Departement, Commune.id_departement == Departement.id_departement
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                Departement.id_region == id_region,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Candidat.nom_candidat).all()

        # Calculer le total des voix pour cette région
        total_voix_region = sum(row.total_voix or 0 for row in query)

        # Créer les résultats par candidat
        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.total_voix or 0,
                pourcentage=_calculer_pourcentage(row.total_voix or 0, total_voix_region),
            )
            resultats_candidats.append(stat_candidat)

        # Créer la statistique globale pour la région
        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_region,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats pour la région {id_region}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_resultats_departement_specifique(
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de résultats pour un département spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le département existe
        departement = db.query(Departement).filter(
            Departement.id_departement == id_departement
        ).first()

        if not departement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec l'ID {id_departement} introuvable"
            )

        # Requête pour récupérer les statistiques de résultats pour ce département
        query = db.query(
            Candidat.nom_candidat,
            func.sum(ResultatVote.voix).label('total_voix'),
        ).join(
            BureauVote, ResultatVote.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).join(
            Commune, CentreVote.id_commune == Commune.id_commune
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                Commune.id_departement == id_departement,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Candidat.nom_candidat).all()

        # Calculer le total des voix pour ce département
        total_voix_departement = sum(row.total_voix or 0 for row in query)

        # Créer les résultats par candidat
        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.total_voix or 0,
                pourcentage=_calculer_pourcentage(row.total_voix or 0, total_voix_departement),
            )
            resultats_candidats.append(stat_candidat)

        # Créer la statistique globale pour le département
        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_departement,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats pour le département {id_departement}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_resultats_commune_specifique(
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de résultats pour une commune spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la commune existe
        commune = db.query(Commune).filter(
            Commune.id_commune == id_commune
        ).first()

        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune avec l'ID {id_commune} introuvable"
            )

        # Requête pour récupérer les statistiques de résultats pour cette commune
        query = db.query(
            Candidat.nom_candidat,
            func.sum(ResultatVote.voix).label('total_voix'),
        ).join(
            BureauVote, ResultatVote.id_bureau == BureauVote.id_bureau
        ).join(
            CentreVote, BureauVote.id_centre == CentreVote.id_centre
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                CentreVote.id_commune == id_commune,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Candidat.nom_candidat).all()

        # Calculer le total des voix pour cette commune
        total_voix_commune = sum(row.total_voix or 0 for row in query)

        # Créer les résultats par candidat
        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.total_voix or 0,
                pourcentage=_calculer_pourcentage(row.total_voix or 0, total_voix_commune),
            )
            resultats_candidats.append(stat_candidat)

        # Créer la statistique globale pour la commune
        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_commune,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats pour la commune {id_commune}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_resultats_centre_specifique(
    id_centre: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de résultats pour un centre de vote spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le centre existe
        centre = db.query(CentreVote).filter(
            CentreVote.id_centre == id_centre
        ).first()

        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre de vote avec l'ID {id_centre} introuvable"
            )

        # Requête pour récupérer les statistiques de résultats pour ce centre
        query = db.query(
            Candidat.nom_candidat,
            func.sum(ResultatVote.voix).label('total_voix'),
        ).join(
            BureauVote, ResultatVote.id_bureau == BureauVote.id_bureau
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                BureauVote.id_centre == id_centre,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Candidat.nom_candidat).all()

        # Calculer le total des voix pour ce centre
        total_voix_centre = sum(row.total_voix or 0 for row in query)

        # Créer les résultats par candidat
        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.total_voix or 0,
                pourcentage=_calculer_pourcentage(row.total_voix or 0, total_voix_centre),
            )
            resultats_candidats.append(stat_candidat)

        # Créer la statistique globale pour le centre
        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_centre,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats pour le centre : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_statistiques_resultats_bureau_specifique(
    id_bureau: int,
    id_election: int,
    date_election: date,
    db: Session
):
    """
    Récupère les statistiques de résultats pour un bureau de vote spécifique.
    """
    try:
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le bureau existe
        bureau = db.query(BureauVote).filter(
            BureauVote.id_bureau == id_bureau
        ).first()

        if not bureau:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bureau avec l'ID {id_bureau} introuvable"
            )

        # Requête pour récupérer les statistiques de résultats pour ce bureau
        query = db.query(
            Candidat.nom_candidat,
            ResultatVote.voix
        ).join(
            Candidat, ResultatVote.id_candidat == Candidat.id_candidat
        ).filter(
            and_(
                ResultatVote.id_bureau == id_bureau,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).all()

        # Calculer le total des voix pour ce bureau
        total_voix_bureau = sum(row.voix or 0 for row in query)

        # Créer les résultats par candidat
        resultats_candidats = []
        for row in query:
            stat_candidat = StatistiquesResultat(
                nom_candidat=row.nom_candidat,
                total_voix=row.voix or 0,
                pourcentage=_calculer_pourcentage(row.voix or 0, total_voix_bureau),
            )
            resultats_candidats.append(stat_candidat)

        # Créer la statistique globale pour le bureau
        stat_globale = StatistiquesResultatGlobal(
            total_voix_global=total_voix_bureau,
            resultats_candidats=resultats_candidats
        )

        return stat_globale

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques de résultats pour le bureau {id_bureau}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


def get_votes_candidat_par_region(
    id_candidat: int,
    id_election: int,
    date_election: date,
    db: Session
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par région.

    Args:
        id_candidat: ID du candidat
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des régions comme clés
                       et le nombre de votes comme valeurs

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier que le candidat existe
        candidat = db.query(Candidat).filter(
            Candidat.id_candidat == id_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {id_candidat} introuvable"
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Requête pour récupérer les votes par région
        query = db.query(
            Region.nom_region,
            func.sum(ResultatVote.voix).label('total_voix')
        ).join(
            Departement, Region.id_region == Departement.id_region
        ).join(
            Commune, Departement.id_departement == Commune.id_departement
        ).join(
            CentreVote, Commune.id_commune == CentreVote.id_commune
        ).join(
            BureauVote, CentreVote.id_centre == BureauVote.id_centre
        ).join(
            ResultatVote, BureauVote.id_bureau == ResultatVote.id_bureau
        ).filter(
            and_(
                ResultatVote.id_candidat == id_candidat,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Region.nom_region).all()

        # Créer le dictionnaire de résultats
        votes_par_region = {}
        for row in query:
            votes_par_region[row.nom_region] = row.total_voix or 0

        logger.info(f"Récupération des votes pour le candidat {candidat.nom_candidat} par région")
        return votes_par_region

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des votes par région pour le candidat {id_candidat}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des votes par région"
        )




def get_votes_candidat_par_departement(
    id_candidat: int,
    id_region: int,
    id_election: int,
    date_election: date,
    db: Session
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par département dans une région donnée.

    Args:
        id_candidat: ID du candidat
        id_region: ID de la région
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des départements comme clés
                       et le nombre de votes comme valeurs

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier que le candidat existe
        candidat = db.query(Candidat).filter(
            Candidat.id_candidat == id_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {id_candidat} introuvable"
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la région existe
        region = db.query(Region).filter(
            Region.id_region == id_region
        ).first()

        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Région avec l'ID {id_region} introuvable"
            )

        # Requête pour récupérer les votes par département dans la région spécifiée
        query = db.query(
            Departement.nom_departement,
            func.sum(ResultatVote.voix).label('total_voix')
        ).join(
            Commune, Departement.id_departement == Commune.id_departement
        ).join(
            CentreVote, Commune.id_commune == CentreVote.id_commune
        ).join(
            BureauVote, CentreVote.id_centre == BureauVote.id_centre
        ).join(
            ResultatVote, BureauVote.id_bureau == ResultatVote.id_bureau
        ).filter(
            and_(
                Departement.id_region == id_region,
                ResultatVote.id_candidat == id_candidat,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Departement.nom_departement).all()

        # Créer le dictionnaire de résultats
        votes_par_departement = {}
        for row in query:
            votes_par_departement[row.nom_departement] = row.total_voix or 0

        logger.info(f"Récupération des votes pour le candidat {candidat.nom_candidat} par département dans la région {region.nom_region}")
        return votes_par_departement

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des votes par département pour le candidat {id_candidat} dans la région {id_region}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des votes par département"
        )


def get_votes_candidat_par_commune(
    id_candidat: int,
    id_departement: int,
    id_election: int,
    date_election: date,
    db: Session
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par commune dans un département donné.

    Args:
        id_candidat: ID du candidat
        id_departement: ID du département
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des communes comme clés
                       et le nombre de votes comme valeurs

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier que le candidat existe
        candidat = db.query(Candidat).filter(
            Candidat.id_candidat == id_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {id_candidat} introuvable"
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le département existe
        departement = db.query(Departement).filter(
            Departement.id_departement == id_departement
        ).first()

        if not departement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec l'ID {id_departement} introuvable"
            )

        # Requête pour récupérer les votes par commune dans le département spécifié
        query = db.query(
            Commune.nom_commune,
            func.sum(ResultatVote.voix).label('total_voix')
        ).join(
            CentreVote, Commune.id_commune == CentreVote.id_commune
        ).join(
            BureauVote, CentreVote.id_centre == BureauVote.id_centre
        ).join(
            ResultatVote, BureauVote.id_bureau == ResultatVote.id_bureau
        ).filter(
            and_(
                Commune.id_departement == id_departement,
                ResultatVote.id_candidat == id_candidat,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(Commune.nom_commune).all()

        # Créer le dictionnaire de résultats
        votes_par_commune = {}
        for row in query:
            votes_par_commune[row.nom_commune] = row.total_voix or 0

        logger.info(f"Récupération des votes pour le candidat {candidat.nom_candidat} par commune dans le département {departement.nom_departement}")
        return votes_par_commune

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des votes par commune pour le candidat {id_candidat} dans le département {id_departement}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des votes par commune"
        )


def get_votes_candidat_par_centre(
    id_candidat: int,
    id_commune: int,
    id_election: int,
    date_election: date,
    db: Session
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par centre dans une commune donnée.

    Args:
        id_candidat: ID du candidat
        id_commune: ID de la commune
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, int]: Dictionnaire avec les noms des centres comme clés
                       et le nombre de votes comme valeurs

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier que le candidat existe
        candidat = db.query(Candidat).filter(
            Candidat.id_candidat == id_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {id_candidat} introuvable"
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que la commune existe
        commune = db.query(Commune).filter(
            Commune.id_commune == id_commune
        ).first()

        if not commune:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Commune avec l'ID {id_commune} introuvable"
            )

        # Requête pour récupérer les votes par centre dans la commune spécifiée
        query = db.query(
            CentreVote.nom_centre,
            func.sum(ResultatVote.voix).label('total_voix')
        ).join(
            BureauVote, CentreVote.id_centre == BureauVote.id_centre
        ).join(
            ResultatVote, BureauVote.id_bureau == ResultatVote.id_bureau
        ).filter(
            and_(
                CentreVote.id_commune == id_commune,
                ResultatVote.id_candidat == id_candidat,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).group_by(CentreVote.nom_centre).all()

        # Créer le dictionnaire de résultats
        votes_par_centre = {}
        for row in query:
            votes_par_centre[row.nom_centre] = row.total_voix or 0

        logger.info(f"Récupération des votes pour le candidat {candidat.nom_candidat} par centre dans la commune {commune.nom_commune}")
        return votes_par_centre

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des votes par centre pour le candidat {id_candidat} dans la commune {id_commune}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des votes par centre"
        )


def get_votes_candidat_par_bureau(
    id_candidat: int,
    id_centre: int,
    id_election: int,
    date_election: date,
    db: Session
) -> Dict[str, int]:
    """
    Récupère le nombre de votes pour un candidat spécifique par bureau dans un centre donné.

    Args:
        id_candidat: ID du candidat
        id_centre: ID du centre de vote
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        db: Session de base de données

    Returns:
        Dict[str, int]: Dictionnaire avec les numéros de bureau comme clés (format "Bureau X")
                       et le nombre de votes comme valeurs

    Raises:
        HTTPException: En cas d'erreur
    """
    try:
        # Vérifier que le candidat existe
        candidat = db.query(Candidat).filter(
            Candidat.id_candidat == id_candidat
        ).first()

        if not candidat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidat avec l'ID {id_candidat} introuvable"
            )

        # Vérifier que l'élection existe
        election = db.query(Election).filter(
            Election.id_election == id_election
        ).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Élection avec l'ID {id_election} introuvable"
            )

        # Vérifier que le centre existe
        centre = db.query(CentreVote).filter(
            CentreVote.id_centre == id_centre
        ).first()

        if not centre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Centre de vote avec l'ID {id_centre} introuvable"
            )

        # Requête pour récupérer les votes par bureau dans le centre spécifié
        query = db.query(
            BureauVote.numero_bureau,
            ResultatVote.voix
        ).join(
            ResultatVote, BureauVote.id_bureau == ResultatVote.id_bureau
        ).filter(
            and_(
                BureauVote.id_centre == id_centre,
                ResultatVote.id_candidat == id_candidat,
                ResultatVote.id_election == election.id_election,
                ResultatVote.date_election == date_election
            )
        ).order_by(BureauVote.numero_bureau).all()

        # Créer le dictionnaire de résultats
        votes_par_bureau = {}
        for row in query:
            votes_par_bureau[f"Bureau {row.numero_bureau}"] = row.voix or 0

        logger.info(f"Récupération des votes pour le candidat {candidat.nom_candidat} par bureau dans le centre {centre.nom_centre}")
        return votes_par_bureau

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des votes par bureau pour le candidat {id_candidat} dans le centre {id_centre}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des votes par bureau"
        )


