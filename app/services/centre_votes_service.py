"""Service pour la gestion des centres de vote."""

from sqlalchemy.orm import Session
from app.schema.centre_votes_schema import CentreVotesSchema, CentreVotesReponse
from app.model.centres_votes_model import CentreVote
from app.model.commune_model import Commune
from fastapi import HTTPException, status


def get_all_centres(page,limit,db: Session):
    """Récupère tous les centres de vote avec leurs bureaux."""
    offset = (page-1)*limit
    result = db.query(CentreVote).offset(offset).limit(limit).all()
    total = db.query(CentreVote).count()
    centres = [
        CentreVotesReponse(
            id_centre=c.id_centre,
            nom_centre=c.nom_centre,
            id_commune=c.id_commune,
            nombre_bureaux=len(c.bureaux_vote),
            bureaux_vote=c.bureaux_vote
        )
        for c in result
    ]

    return {"data":centres,"total":total}

def get_all_centres_without_pagination(db: Session):
    """Récupère tous les centres de vote avec leurs bureaux."""
    result = db.query(CentreVote).all()
    centres = [
        CentreVotesReponse(
            id_centre=c.id_centre,
            nom_centre=c.nom_centre,
            id_commune=c.id_commune,
            nombre_bureaux=len(c.bureaux_vote),
            bureaux_vote=c.bureaux_vote
        )
        for c in result
    ]

    return centres



def create_centre(request: CentreVotesSchema, db: Session):
    """Crée un nouveau centre de vote."""
    # Vérifier si le centre existe déjà dans cette commune
    existing = (
        db.query(CentreVote)
        .filter(
            CentreVote.nom_centre == request.nom_centre,
            CentreVote.id_commune == request.id_commune
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le centre '{request.nom_centre}' existe déjà dans cette commune."
        )

    # Vérifier que la commune existe
    commune = db.query(Commune).filter(Commune.id_commune == request.id_commune).first()
    if not commune:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {request.id_commune} introuvable"
        )

    # Créer le centre
    centre = CentreVote(**request.model_dump())
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


def get_centre_by_id(id_centre: int, db: Session):
    """Récupère un centre de vote par son ID."""
    centre = db.query(CentreVote).filter(CentreVote.id_centre == id_centre).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre avec l'ID {id_centre} introuvable"
        )
    return centre


def update_centre(id_centre: int, request: CentreVotesSchema, db: Session):
    """Met à jour un centre de vote."""
    centre = db.query(CentreVote).filter(CentreVote.id_centre == id_centre).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre introuvable"
        )

    # Vérifier si la nouvelle combinaison existe déjà (sauf pour lui-même)
    existing = (
        db.query(CentreVote)
        .filter(
            CentreVote.nom_centre == request.nom_centre,
            CentreVote.id_commune == request.id_commune,
            CentreVote.id_centre != id_centre
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un centre avec ce nom existe déjà dans cette commune."
        )

    # Mise à jour
    centre.nom_centre = request.nom_centre
    centre.id_commune = request.id_commune

    db.commit()
    db.refresh(centre)
    return centre


def delete_centre(id_centre: int, db: Session):
    """Supprime un centre de vote."""
    centre = db.query(CentreVote).filter(CentreVote.id_centre == id_centre).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre introuvable"
        )

    # Vérifier s'il y a des bureaux associés
    if len(centre.bureaux_vote) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer le centre. Il contient {len(centre.bureaux_vote)} bureau(x)."
        )

    db.delete(centre)
    db.commit()
    return {"message": "Centre supprimé avec succès"}


def get_centres_by_commune(id_commune: int, db: Session):
    """
    Récupère tous les centres de vote d'une commune spécifique.

    Args:
        id_commune: ID de la commune
        db: Session de base de données

    Returns:
        Liste des centres avec leurs informations

    Raises:
        HTTPException: Si la commune n'existe pas
    """
    # Vérifier que la commune existe
    commune = db.query(Commune).filter(Commune.id_commune == id_commune).first()
    if not commune:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {id_commune} introuvable"
        )

    # Récupérer les centres de cette commune
    centres = db.query(CentreVote).filter(CentreVote.id_commune == id_commune).all()

    centres_list = [
        {
            "id_centre": centre.id_centre,
            "nom_centre": centre.nom_centre,
            "nombre_bureaux": len(centre.bureaux_vote)
        }
        for centre in centres
    ]

    return centres_list


def get_centre_by_nom_centre(nom_centre,db:Session):
    centres = db.query(CentreVote).filter(CentreVote.nom_centre == nom_centre.upper()).all()

    if not centres:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre '{nom_centre}' introuvable"
        )

    result = [
      CentreVotesReponse(
          id_centre=c.id_centre,
          id_commune=c.id_commune,
          nom_centre=c.nom_centre,
          bureaux_vote= c.bureaux_vote,
          nombre_bureaux=len(c.bureaux_vote)
      )
      for c in centres
    ]
    return result

