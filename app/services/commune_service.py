from sqlalchemy.orm import Session
from app.schema.commune_schema import CommuneSchema,CommuneReponse,CommuneReponse1
from app.model.commune_model import Commune
from app.model.centres_votes_model import CentreVote
from sqlalchemy import func
from fastapi import HTTPException,status
from app.model.departement_model import Departement
from fastapi.responses import StreamingResponse



def get_all_commune(page,limit,db: Session):
    offset = (page-1)*limit
    result = db.query(Commune).offset(offset).limit(limit).all()
    total = db.query(Commune).count()

    communes = [
        CommuneReponse(
            id_commune=c.id_commune,
            nom_commune=c.nom_commune,
            id_departement=c.id_departement,
            nombre_centre_vote=len(c.centres_vote),
            centres_vote=c.centres_vote
        )
        for c in result
    ]

    return {"data":communes,"total":total}


def get_all_commune_without_pagination(db: Session):
    result = db.query(Commune).all()

    communes = [
        CommuneReponse(
            id_commune=c.id_commune,
            nom_commune=c.nom_commune,
            id_departement=c.id_departement,
            nombre_centre_vote=len(c.centres_vote),
            centres_vote=c.centres_vote
        )
        for c in result
    ]

    return communes




def create_commune(request: CommuneSchema ,db:Session):
    commune = Commune(**request.model_dump())
    db.add(commune)
    db.commit()
    db.refresh(commune)
    return commune

def update_commune(commune_id: int, commune_request: CommuneSchema, db: Session):
    # Vérifier si la commune existe
    commune = db.query(Commune).filter(Commune.id_commune == commune_id).first()
    if not commune:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec ID {commune_id} introuvable"
        )

    if commune_request.nom_commune is not None:
        commune.nom_commune = commune_request.nom_commune
    if commune_request.id_departement is not None:
        commune.id_departement = commune_request.id_departement

    # Sauvegarder
    db.commit()
    db.refresh(commune)

    return commune


def delete_commune(id: int, db: Session ):
    commune = db.query(Commune).filter(Commune.id_commune == id).first()
    if not commune:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commune introuvable")
    
    db.delete(commune)
    db.commit()
    return {"message": "Commune supprimée avec succès"}

def get_commune_by_departement(id_departement: int, db: Session):
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
    departement = db.query(Departement).filter(Departement.id_departement == id_departement).first()
    if not departement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {id_departement} introuvable"
        )

    # Récupérer les centres de cette commune
    centres = db.query(Commune).filter(Commune.id_departement == id_departement).all()

    centres_list = [
        {
            "id_commune": centre.id_commune,
            "nom_commune": centre.nom_commune,
            "nombre_centre_vote": len(centre.centres_vote)
        }
        for centre in centres
    ]

    return centres_list


def get_centres_for_commune(id_commune,db:Session):
    centres = db.query(CentreVote).filter(CentreVote.id_commune==id_commune).all()
    return centres

def get_communes_by_nom_commune(nom_commune,db:Session):
    commune = db.query(Commune).filter(Commune.nom_commune == nom_commune.upper()).first()

    if not commune:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune '{nom_commune}' introuvable"
        )

    result = CommuneReponse(
          id_commune=commune.id_commune,
          id_departement=commune.id_departement,
          nom_commune=commune.nom_commune,
          centres_vote=commune.centres_vote,
          nombre_centre_vote=len(commune.centres_vote)
      )
    return result