"""
API FastAPI pour la gestion du système électoral.

Cette application fournit une API REST pour gérer les données électorales,
incluant les régions, départements, communes, bureaux de vote et résultats.
"""

from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.services.logger import setup_logger

logger = setup_logger(__name__)

# Import des contrôleurs
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

# Import de la configuration DB
from app.db.connexion import create_tables, health_check,drop_tables

# Import de tous les modèles avant de créer les tables
# import model  # noqa: F401

# Créer les tables au démarrage
try:
    create_tables()
    # drop_tables()
    logger.info("Initialisation de la base de données réussie")
except Exception as e:
    logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    raise

# Configuration de l'application
app = FastAPI(
    title="API Système Électoral",
    description="""
    API REST pour la gestion complète d'un système électoral.

    ## Fonctionnalités

    * **Régions**: Gestion des régions administratives
    * **Départements**: Gestion des départements par région
    * **Communes**: Gestion des communes par département
    * **Bureaux de vote**: Gestion des centres et bureaux de vote
    * **Élections**: Gestion des données électorales et résultats

    ## Authentification

    L'API utilise actuellement un accès libre pour le développement.

    ## Versions

    * **v1**: Version actuelle avec toutes les fonctionnalités de base
    """,
    version="1.0.0",
    contact={
        "name": "Équipe Développement Électoral",
        "email": "contact@elections.sn",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
ALLOWED_ORIGINS = [
    "*",   # React dev server
]



from middleware.logging_middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)


# Gestionnaires d'erreurs globaux
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Gestionnaire pour les erreurs de validation des requêtes."""
    logger.warning(f"Erreur de validation sur {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erreur de validation des données",
            "errors": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Gestionnaire pour les erreurs de base de données."""
    logger.error(f"Erreur de base de données sur {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erreur interne du serveur",
            "message": "Une erreur de base de données s'est produite"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Gestionnaire pour toutes les autres erreurs."""
    logger.error(f"Erreur non gérée sur {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erreur interne du serveur",
            "message": "Une erreur inattendue s'est produite"
        }
    )


# Routes de base
@app.get(
    "/",
    summary="Page d'accueil de l'API",
    description="Point d'entrée principal de l'API avec informations de base"
)
async def root() -> Dict[str, Any]:
    """
    Page d'accueil de l'API.

    Returns:
        Dict contenant les informations de base de l'API
    """
    return {
        "message": "API Système Électoral",
        "version": "1.0.0",
        "status": "actif",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get(
    "/health",
    summary="Vérification de l'état de l'API",
    description="Endpoint pour vérifier l'état de l'API et de la base de données"
)
async def health_check_endpoint() -> Dict[str, Any]:
    """
    Vérifie l'état de l'API et de ses dépendances.

    Returns:
        Dict contenant l'état de l'API et de la base de données
    """
    db_status = health_check()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": "2025-01-21T00:00:00Z",  # Sera remplacé par datetime.utcnow()
        "version": "1.0.0"
    }



app.include_router(
    regions_router,
    tags=["Régions"]
)

app.include_router(
    departement_router,
    tags=["Départements"]
)

app.include_router(
    commune_router,
    tags=["Communes"]
)

app.include_router(
    centre_vote_router,
    tags=["Centres de Vote"]
)

app.include_router(
    bureau_vote_router,
    tags=["Bureaux de Vote"]
)

app.include_router(
    elections_router,
    tags=["Élections"]
)

app.include_router(
    participation_router,
    tags=["Participations"]
)

app.include_router(
    resultat_vote_router,
    tags=["Résultats de vote"]
)

app.include_router(
    candidat_router,
    tags=["Candidats"]
)

app.include_router(
    inscription_election_router,
    tags=["Inscriptions d'élection"]
)


# Events de l'application
@app.on_event("startup")
async def startup_event():
    """Événement exécuté au démarrage de l'application."""
    logger.info("🚀 API Système Électoral démarrée")
    logger.info("📚 Documentation disponible sur /docs")

    # Vérifier la connexion DB
    if health_check():
        logger.info("✅ Connexion à la base de données OK")
    else:
        logger.error("❌ Problème de connexion à la base de données")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement exécuté à l'arrêt de l'application."""
    logger.info("🛑 Arrêt de l'API Système Électoral")

