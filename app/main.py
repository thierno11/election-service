from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from prometheus_fastapi_instrumentator import Instrumentator

from app.services.logger import setup_logger
from app.middleware.logging_middleware import RequestLoggingMiddleware

# Routers
from app.controller.regions_controllers import regions_router
from app.controller.deparetements_controllers import departement_router
from app.controller.commune_controller import commune_router
from app.controller.centres_votes_controller import centre_vote_router
from app.controller.bureau_vote_controller import bureau_vote_router
from app.controller.elections_controller import elections_router
from app.controller.participation_controller import participation_router
from app.controller.resultat_vote_controller import resultat_vote_router
from app.controller.candidat_controller import candidat_router
from app.controller.inscription_election_controller import inscription_election_router

# Database
from app.db.connexion import create_tables, drop_tables, health_check

logger = setup_logger(__name__)


instrumentator =Instrumentator()

# ------------------------------------------------------------
# LIFESPAN MODERNE (remplace on_event startup/shutdown)
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- Startup ----------
    logger.info("🚀 API Système Électoral démarrée")
    try:
        create_tables()
        logger.info("📌 Tables DB OK")
    except Exception as e:
        logger.error(f"❌ Erreur creation tables: {e}")
        raise

    if health_check():
        logger.info("✅ Connexion DB OK")
    else:
        logger.error("❌ Connexion DB KO")

    # Exposer Prometheus après startup
    # instrumentator.instrument(app).expose(app, endpoint="/metrics")

    yield  # ⬅️ point où l'app tourne

    # ---------- Shutdown ----------
    logger.info("🛑 API Système Électoral arrêtée")


# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title="API Système Électoral",
    description="API REST pour gérer un système électoral complet.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ------------------------------------------------------------
# MIDDLEWARES
# ------------------------------------------------------------
app.add_middleware(RequestLoggingMiddleware)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_credentials=True,
# )

# ------------------------------------------------------------
# ERROR HANDLERS
# ------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Erreur validation {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Erreur de validation", "errors": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Erreur DB sur {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne", "message": "Erreur base de données"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur serveur sur {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne", "message": "Erreur inattendue"},
    )


# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "API Système Électoral",
        "version": "1.0.0",
        "health": "/health",
        "metrics": "/metrics",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check_endpoint():
    db_ok = health_check()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
    }
instrumentator.instrument(app).expose(app, endpoint="/metrics")



# Routers
app.include_router(regions_router, tags=["Régions"])
app.include_router(departement_router, tags=["Départements"])
app.include_router(commune_router, tags=["Communes"])
app.include_router(centre_vote_router, tags=["Centres de Vote"])
app.include_router(bureau_vote_router, tags=["Bureaux de Vote"])
app.include_router(elections_router, tags=["Élections"])
app.include_router(participation_router, tags=["Participations"])
app.include_router(resultat_vote_router, tags=["Résultats"])
app.include_router(candidat_router, tags=["Candidats"])
app.include_router(inscription_election_router, tags=["Inscriptions"])