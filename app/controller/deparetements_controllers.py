from fastapi import APIRouter,Depends,Query
from app.services.departements_service import  Session,create_departement,get_all_departement,delete_departement,update_departement,get_commmune_for_departement,get_all_departement_without_pagibnation
from app.db.connexion import get_database
from app.schema.departement_schema import DepartementReponse,DepartementSchema
from typing import List

departement_router = APIRouter(prefix="/elections/departements")

@departement_router.post("/")
def creer_departement(request:DepartementSchema,db:Session=(Depends(get_database))):
    return create_departement(request,db)

@departement_router.get("/")
def recuperer_departements(page:int = Query(1,ge=1),limit:int = Query(10,ge=10,le=100),db:Session=Depends(get_database)):
    return get_all_departement(page,limit,db)


@departement_router.get("/all")
def recuperer_departements_all(db:Session=Depends(get_database)):
    return get_all_departement_without_pagibnation(db)

@departement_router.put("/{id}")
def modifier_departement(id,request:DepartementSchema,db:Session=(Depends(get_database))):
    return update_departement(id,request,db)

@departement_router.delete("/{id}")
def supprimer_departement(id:int,db:Session=Depends(get_database)):
    return delete_departement(id,db)

@departement_router.get("/{id_departement}/communes")
def get_communes_for_departement(id_departement:int,db:Session=Depends(get_database)):
    return get_commmune_for_departement(id_departement,db)