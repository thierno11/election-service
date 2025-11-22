"""Configuration de la connexion à la base de données."""

import logging
import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()


class DatabaseConfig:
    """Configuration centralisée pour la base de données."""

    def __init__(self) -> None:
        """Initialise la configuration de la base de données."""
        self.user: str = os.getenv("DB_USER", "")
        self.password: str = os.getenv("DB_PASSWORD", "")
        self.host: str = os.getenv("DB_HOST", "localhost")
        self.port: str = os.getenv("DB_PORT", "5432")
        self.db_name: str = os.getenv("DB_NAME", "elections")
        self.echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"

        # Validation des paramètres requis
        if not self.user or not self.password:
            raise ValueError("DB_USER et DB_PASSWORD doivent être définis dans les variables d'environnement")

    @property
    def database_url(self) -> str:
        """
        Construit l'URL de connexion à la base de données.

        Returns:
            str: URL de connexion PostgreSQL
        """
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"

    def create_engine(self) -> Engine:
        """
        Crée le moteur SQLAlchemy.

        Returns:
            Engine: Moteur SQLAlchemy configuré
        """
        try:
            engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "Elections_Backend"
                }
            )
            logger.info(f"Moteur de base de données créé pour {self.host}:{self.port}/{self.db_name}")
            return engine
        except Exception as e:
            logger.error(f"Erreur lors de la création du moteur de base de données: {e}")
            raise


# Configuration globale
config = DatabaseConfig()
engine = config.create_engine()

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def get_database() -> Generator[Session, None, None]:
    """
    Générateur de session de base de données pour FastAPI.

    Yields:
        Session: Session SQLAlchemy

    Raises:
        SQLAlchemyError: En cas d'erreur de base de données
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Erreur de base de données: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """
    Crée toutes les tables de la base de données.

    Raises:
        SQLAlchemyError: En cas d'erreur lors de la création des tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        raise


def drop_tables() -> None:
    """
    Supprime toutes les tables de la base de données.

    Warning:
        Cette fonction supprime définitivement toutes les données!

    Raises:
        SQLAlchemyError: En cas d'erreur lors de la suppression des tables
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("Toutes les tables ont été supprimées")
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la suppression des tables: {e}")
        raise


def get_session() -> Session:
    """
    Crée une nouvelle session de base de données.

    Returns:
        Session: Nouvelle session SQLAlchemy

    Note:
        Cette fonction est utile pour les scripts et les tests.
        Pour FastAPI, utilisez get_database() comme dépendance.
    """
    return SessionLocal()


def health_check() -> bool:
    """
    Vérifie la connexion à la base de données.

    Returns:
        bool: True si la connexion fonctionne, False sinon
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Connexion à la base de données OK")
        return True
    except Exception as e:
        logger.error(f"Échec de la connexion à la base de données: {e}")
        return False

