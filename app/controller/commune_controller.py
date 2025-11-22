from fastapi import APIRouter,Depends,Query
from app.services.commune_service import create_commune,get_all_commune,Session,update_commune,delete_commune,get_commune_by_departement,Commune,get_centres_for_commune,get_all_commune_without_pagination
from app.db.connexion import get_database
from app.schema.commune_schema import CommuneReponse,CommuneSchema
from fastapi.responses import StreamingResponse
import json


commune_router = APIRouter(prefix="/elections/communes",tags=["Communes"])

@commune_router.post("/")
def creer_commune(request:CommuneSchema,db:Session=Depends(get_database)):
    return create_commune(request,db)

@commune_router.get("/")
def recuperer_commune(page:int = Query(1,ge=1),limit:int = Query(10,ge=10,le=100),db:Session=Depends(get_database)):
    return get_all_commune(page,limit,db)

@commune_router.get("/all")
def recuperer_commune_all(db:Session=Depends(get_database)):
    return get_all_commune_without_pagination(db)


@commune_router.get("/stream")
def get_all_commune_stream(db: Session = Depends(get_database)):
    def commune_generator():
        # ⚠️ Ici, on itère sur un query, pas .all()
        for c in db.query(Commune):
            commune_data = CommuneReponse(
                id_commune=c.id_commune,
                nom_commune=c.nom_commune,
                id_departement=c.id_departement,
                nombre_centre_vote=len(c.centres_vote),
                centres_vote=c.centres_vote
            ).model_dump()  # ou .dict() selon ta version de Pydantic
            
            # On convertit en JSON + saut de ligne
            yield json.dumps(commune_data) + "\n"
    
    return StreamingResponse(commune_generator(), media_type="application/json")

@commune_router.put("/{id}")
def modifier_commune(id:int,request:CommuneSchema,db:Session=Depends(get_database)):
    return update_commune(commune_id=id,commune_request=request,db=db)

@commune_router.delete("/{id}",)
def supprimer_commune(id: int, db: Session = Depends(get_database)):
    return delete_commune(id,db)

@commune_router.get("/departement/{id_departement}",)
def supprimer_commune(id_departement: int, db: Session = Depends(get_database)):
    return get_commune_by_departement(id_departement,db)



@commune_router.get("/{id_commune}/centres")
def get_centres_by_commune(id_commune:int,db:Session=Depends(get_database)):
    return get_centres_for_commune(id_commune,db)