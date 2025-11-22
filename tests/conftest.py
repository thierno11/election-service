import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from db.connexion import Base, get_database
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def client(test_db_session):
    def override_get_database():
        try:
            yield test_db_session
        finally:
            pass  # Don't close here as it's handled in test_db_session fixture

    app.dependency_overrides[get_database] = override_get_database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()