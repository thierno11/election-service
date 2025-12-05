"""Service pour la gestion des résultats de vote."""

import logging
from typing import  List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from app.services.commune_service import  get_communes_by_nom_commune

from app.model.resultat_model import ResultatVote
from app.model.election_model import Election
from app.model.candidat_model import Candidat
from app.model.centres_votes_model import CentreVote
from app.schema.resultat_vote_schema import (
    ResultatVoteBulkSchema,
)

logger = logging.getLogger(__name__)



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
