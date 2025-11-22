"""Service pour la gestion des bureaux de vote."""

from sqlalchemy.orm import Session
from app.schema.bureau_vote_schema import BureauVoteSchema, BureauVoteReponse
from app.model.bureau_vote import BureauVote
from app.model.centres_votes_model import CentreVote
from fastapi import HTTPException, status


def get_all_bureaux(page,limit,db: Session):
    """Récupère tous les bureaux de vote avec leurs centres."""
    offset = (page - 1) * limit
    total = db.query(BureauVote).count()
    result = db.query(BureauVote)\
          .offset(offset)\
          .limit(limit)\
          .all()

    bureaux = [
        BureauVoteReponse(
            id_bureau=b.id_bureau,
            numero_bureau=b.numero_bureau,
            implantation=b.implantation,
            id_centre=b.id_centre,
            centre_vote= b.centre_vote
        )
        for b in result
    ]

    return {"data": bureaux, "total": total}


def create_bureau(request: BureauVoteSchema, db: Session):
    """Crée un nouveau bureau de vote."""
    # Vérifier si le bureau existe déjà dans ce centre
    existing = (
        db.query(BureauVote)
        .filter(
            BureauVote.numero_bureau == request.numero_bureau,
            BureauVote.id_centre == request.id_centre
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le bureau numéro {request.numero_bureau} existe déjà dans ce centre."
        )

    # Vérifier que le centre existe
    centre = db.query(CentreVote).filter(CentreVote.id_centre == request.id_centre).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre avec l'ID {request.id_centre} introuvable"
        )

    # Créer le bureau
    bureau = BureauVote(**request.model_dump())
    db.add(bureau)
    db.commit()
    db.refresh(bureau)
    return bureau


def get_bureau_by_id(id_bureau: int, db: Session):
    """Récupère un bureau de vote par son ID."""
    bureau = db.query(BureauVote).filter(BureauVote.id_bureau == id_bureau).first()
    if not bureau:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bureau avec l'ID {id_bureau} introuvable"
        )
    return bureau


def update_bureau(id_bureau: int, request: BureauVoteSchema, db: Session):
    """Met à jour un bureau de vote."""
    bureau = db.query(BureauVote).filter(BureauVote.id_bureau == id_bureau).first()
    if not bureau:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bureau introuvable"
        )

    # Vérifier si la nouvelle combinaison existe déjà (sauf pour lui-même)
    existing = (
        db.query(BureauVote)
        .filter(
            BureauVote.numero_bureau == request.numero_bureau,
            BureauVote.id_centre == request.id_centre,
            BureauVote.id_bureau != id_bureau
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un bureau avec ce numéro existe déjà dans ce centre."
        )

    # Mise à jour
    bureau.numero_bureau = request.numero_bureau
    bureau.implantation = request.implantation
    bureau.id_centre = request.id_centre

    db.commit()
    db.refresh(bureau)
    return bureau


def delete_bureau(id_bureau: int, db: Session):
    """Supprime un bureau de vote."""
    bureau = db.query(BureauVote).filter(BureauVote.id_bureau == id_bureau).first()
    if not bureau:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bureau introuvable"
        )

    db.delete(bureau)
    db.commit()
    return {"message": "Bureau supprimé avec succès"}


def get_bureaux_by_centre(id_centre: int, db: Session):
    """
    Récupère tous les bureaux de vote d'un centre spécifique.

    Args:
        id_centre: ID du centre de vote
        db: Session de base de données

    Returns:
        Liste des bureaux avec leurs informations

    Raises:
        HTTPException: Si le centre n'existe pas
    """
    # Vérifier que le centre existe
    centre = db.query(CentreVote).filter(CentreVote.id_centre == id_centre).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre avec l'ID {id_centre} introuvable"
        )

    # Récupérer tous les bureaux du centre
    bureaux = (
        db.query(BureauVote)
        .filter(BureauVote.id_centre == id_centre)
        .order_by(BureauVote.numero_bureau)
        .all()
    )

    bureaux_list = [
        {
            "id_bureau": bureau.id_bureau,
            "numero_bureau": bureau.numero_bureau,
            "implantation": bureau.implantation,
            "id_centre": bureau.id_centre
        }
        for bureau in bureaux
    ]

    return bureaux_list
