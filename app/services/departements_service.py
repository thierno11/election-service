from sqlalchemy.orm import Session
from app.model.departement_model import Departement
from app.model.commune_model import Commune
from app.schema.departement_schema import DepartementSchema,DepartementReponse
from fastapi import HTTPException,status
from sqlalchemy import func




def create_departement(departement_request: DepartementSchema, db: Session):
    # Vérifier si le département existe déjà dans la même région
    existing_departement = (
        db.query(Departement)
        .filter(
            Departement.nom_departement == departement_request.nom_departement,
            Departement.id_region == departement_request.id_region
        )
        .first()
    )

    if existing_departement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le département '{departement_request.nom_departement}' existe déjà dans cette région."
        )

    # Création du département
    departement = Departement(**departement_request.model_dump())
    db.add(departement)
    db.commit()
    db.refresh(departement)
    return departement

def get_all_departement(page,limit,db:Session):
    offset = (page - 1) *limit
    result = db.query(Departement).offset(offset).limit(limit).all()
    total = db.query(Departement).count()
    departements = [
        DepartementReponse(
            id_departement=d.id_departement,
            nom_departement=d.nom_departement,
            id_region=d.id_region,
            nombre_commune=len(d.communes),
            communes=d.communes
        )
        for d in result
    ]

    return {"data":departements,"total":total}
    

def get_all_departement_without_pagibnation(db:Session):
    result = db.query(Departement).all()
    departements = [
        DepartementReponse(
            id_departement=d.id_departement,
            nom_departement=d.nom_departement,
            id_region=d.id_region,
            nombre_commune=len(d.communes),
            communes=d.communes
        )
        for d in result
    ]

    return departements
    


def update_departement(id_departement: int, departement_request: DepartementSchema, db: Session):
    # Vérifier si le département existe
    departement = db.query(Departement).filter(Departement.id_departement == id_departement).first()
    if not departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Département introuvable")

    # Vérifier si le nouveau nom existe déjà (si on veut le modifier)
    if departement_request.nom_departement != departement.nom_departement:
        existing = db.query(Departement).filter(Departement.nom_departement == departement_request.nom_departement).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom du département déjà utilisé")

    # Mise à jour des champs
    if departement_request.nom_departement is not None:
        departement.nom_departement = departement_request.nom_departement
    if departement_request.id_region is not None:
        departement.id_region = departement_request.id_region

    db.commit()
    db.refresh(departement)

    return departement

  



def delete_departement(id_departement: int, db: Session):
    # Vérifier si le département existe
    departement = db.query(Departement).filter(Departement.id_departement == id_departement).first()
    if not departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Département introuvable")
    
    # Supprimer le département
    db.delete(departement)
    db.commit()
    
    return {"message": "Département supprimé avec succès"}


def get_commmune_for_departement(id_departement,db:Session):
    departements = db.query(Commune).filter(Commune.id_departement==id_departement).all()
    return departements