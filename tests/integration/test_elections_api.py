"""Tests d'intégration pour l'API des élections."""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from model.election_model import Election


class TestElectionsAPI:
    """Tests d'intégration pour l'API de gestion des élections."""

    @pytest.fixture
    def client(self):
        """Client de test FastAPI."""
        return TestClient(app)

    def test_create_election_success(self, client, test_db_session):
        """Test de création d'une élection via l'API."""
        future_date = date.today() + timedelta(days=30)

        election_data = {
            "type_election": "presidentielle",
            "nom_election": "Élection Présidentielle API Test",
            "description": "Test d'élection via API",
            "date_election": future_date.isoformat(),
            "statut": "programmee",
            "nombre_tours": 2,
            "tour_actuel": 1,
            "active": True
        }

        response = client.post("/elections/", json=election_data)

        assert response.status_code == 201
        data = response.json()
        assert data["nom_election"] == "Élection Présidentielle Api Test"  # Title case
        assert data["type_election"] == "presidentielle"
        assert data["nombre_tours"] == 2
        assert data["active"] is True
        assert "id_election" in data

    def test_create_election_invalid_data(self, client):
        """Test de création d'une élection avec données invalides."""
        # Date dans le passé
        past_date = date.today() - timedelta(days=1)

        election_data = {
            "type_election": "presidentielle",
            "nom_election": "Test",  # Trop court
            "date_election": past_date.isoformat(),
            "tour_actuel": 3,  # Plus grand que nombre_tours
            "nombre_tours": 2
        }

        response = client.post("/elections/", json=election_data)

        assert response.status_code == 422
        errors = response.json()["errors"]
        error_fields = [error["loc"][-1] for error in errors]

        assert "nom_election" in error_fields  # Nom trop court
        assert "date_election" in error_fields  # Date dans le passé
        assert "tour_actuel" in error_fields  # Tour actuel > nombre tours

    def test_create_election_duplicate_name(self, client, test_db_session):
        """Test de création d'une élection avec nom existant."""
        future_date = date.today() + timedelta(days=30)

        # Créer une élection directement en DB
        existing_election = Election(
            type_election="presidentielle",
            nom_election="Election Existante",
            date_election=future_date
        )
        test_db_session.add(existing_election)
        test_db_session.commit()

        # Tenter de créer une élection avec le même nom
        election_data = {
            "type_election": "legislative",
            "nom_election": "Election Existante",
            "date_election": future_date.isoformat()
        }

        response = client.post("/elections/", json=election_data)

        assert response.status_code == 400
        assert "Election Existante" in response.json()["detail"]

    def test_get_all_elections(self, client, test_db_session):
        """Test de récupération de toutes les élections."""
        future_date1 = date.today() + timedelta(days=10)
        future_date2 = date.today() + timedelta(days=20)

        # Créer des élections de test
        election1 = Election(
            type_election="presidentielle",
            nom_election="Election 1",
            date_election=future_date1,
            active=True
        )

        election2 = Election(
            type_election="legislative",
            nom_election="Election 2",
            date_election=future_date2,
            active=True,
            statut="en_cours"
        )

        election3 = Election(
            type_election="locale",
            nom_election="Election Inactive",
            date_election=future_date1,
            active=False
        )

        test_db_session.add_all([election1, election2, election3])
        test_db_session.commit()

        # Test sans filtres (active_only=True par défaut)
        response = client.get("/elections/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["nom_election"] == "Election 2"  # Plus récente en premier

        # Test avec active_only=False
        response = client.get("/elections/?active_only=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test avec filtre par type
        response = client.get("/elections/?type_election=presidentielle")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type_election"] == "presidentielle"

        # Test avec filtre par statut
        response = client.get("/elections/?statut=en_cours")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["statut"] == "en_cours"

        # Test avec pagination
        response = client.get("/elections/?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_search_elections(self, client, test_db_session):
        """Test de recherche d'élections."""
        future_date = date.today() + timedelta(days=30)

        # Créer des élections de test
        election1 = Election(
            type_election="presidentielle",
            nom_election="Élection Présidentielle 2024",
            description="Grande élection nationale",
            date_election=future_date,
            active=True
        )

        election2 = Election(
            type_election="legislative",
            nom_election="Élections Législatives",
            description="Elections pour le parlement",
            date_election=future_date,
            active=True
        )

        test_db_session.add_all([election1, election2])
        test_db_session.commit()

        # Recherche par nom
        response = client.get("/elections/search?q=présidentielle")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Présidentielle" in data[0]["nom_election"]

        # Recherche par type
        response = client.get("/elections/search?q=legislative")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type_election"] == "legislative"

        # Recherche avec limite
        response = client.get("/elections/search?q=election&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        # Recherche sans résultat
        response = client.get("/elections/search?q=inexistant")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_elections_invalid_query(self, client):
        """Test de recherche avec requête invalide."""
        # Requête trop courte
        response = client.get("/elections/search?q=a")
        assert response.status_code == 422

    def test_get_election_by_id(self, client, test_db_session):
        """Test de récupération d'une élection par ID."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="communale",
            nom_election="Election Test ID",
            description="Test récupération par ID",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()

        response = client.get(f"/elections/{election.id_election}")

        assert response.status_code == 200
        data = response.json()
        assert data["id_election"] == election.id_election
        assert data["nom_election"] == "Election Test ID"
        assert "nombre_resultats" in data
        assert "nombre_participations" in data

    def test_get_election_by_id_not_found(self, client):
        """Test de récupération d'une élection inexistante."""
        response = client.get("/elections/9999")

        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]

    def test_update_election(self, client, test_db_session):
        """Test de mise à jour d'une élection."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="departementale",
            nom_election="Election Originale",
            date_election=future_date,
            nombre_tours=1
        )
        test_db_session.add(election)
        test_db_session.commit()

        new_date = date.today() + timedelta(days=40)
        update_data = {
            "type_election": "departementale",
            "nom_election": "Election Modifiée",
            "date_election": new_date.isoformat(),
            "nombre_tours": 2,
            "tour_actuel": 1
        }

        response = client.put(f"/elections/{election.id_election}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nom_election"] == "Election Modifiée"
        assert data["nombre_tours"] == 2

    def test_update_election_not_found(self, client):
        """Test de mise à jour d'une élection inexistante."""
        future_date = date.today() + timedelta(days=30)

        update_data = {
            "type_election": "presidentielle",
            "nom_election": "Election Inexistante",
            "date_election": future_date.isoformat()
        }

        response = client.put("/elections/9999", json=update_data)

        assert response.status_code == 404

    def test_change_election_status(self, client, test_db_session):
        """Test de changement de statut d'une élection."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="referendum",
            nom_election="Election Statut Test",
            date_election=future_date,
            statut="programmee"
        )
        test_db_session.add(election)
        test_db_session.commit()

        response = client.patch(f"/elections/{election.id_election}/statut?nouveau_statut=en_cours")

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "en_cours"

    def test_change_election_status_invalid(self, client, test_db_session):
        """Test de changement de statut avec statut invalide."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="presidentielle",
            nom_election="Election Statut Invalid",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()

        response = client.patch(f"/elections/{election.id_election}/statut?nouveau_statut=statut_invalide")

        assert response.status_code == 422  # Validation error

    def test_delete_election(self, client, test_db_session):
        """Test de suppression d'une élection."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="regionale",
            nom_election="Election à Supprimer API",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()
        election_id = election.id_election

        response = client.delete(f"/elections/{election_id}")

        assert response.status_code == 200
        data = response.json()
        assert "Election à Supprimer API" in data["message"]
        assert "supprimée avec succès" in data["message"]

        # Vérifier que l'élection n'existe plus
        response_get = client.get(f"/elections/{election_id}")
        assert response_get.status_code == 404

    def test_delete_election_not_found(self, client):
        """Test de suppression d'une élection inexistante."""
        response = client.delete("/elections/9999")

        assert response.status_code == 404

    def test_get_election_types(self, client):
        """Test de récupération des types d'élections disponibles."""
        response = client.get("/elections/types/disponibles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "presidentielle" in data
        assert "legislative" in data
        assert "locale" in data

    def test_get_election_statuses(self, client):
        """Test de récupération des statuts d'élections disponibles."""
        response = client.get("/elections/statuts/disponibles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "programmee" in data
        assert "en_cours" in data
        assert "terminee" in data

    def test_get_election_statistics(self, client, test_db_session):
        """Test de récupération des statistiques globales."""
        future_date = date.today() + timedelta(days=30)

        # Créer des élections de test
        election1 = Election(
            type_election="presidentielle",
            nom_election="Election Stats 1",
            date_election=future_date,
            statut="programmee",
            active=True
        )

        election2 = Election(
            type_election="legislative",
            nom_election="Election Stats 2",
            date_election=future_date,
            statut="en_cours",
            active=True
        )

        election3 = Election(
            type_election="presidentielle",
            nom_election="Election Stats 3",
            date_election=future_date,
            statut="terminee",
            active=False
        )

        test_db_session.add_all([election1, election2, election3])
        test_db_session.commit()

        response = client.get("/elections/statistiques/globales")

        assert response.status_code == 200
        data = response.json()
        assert "total_elections" in data
        assert "elections_actives" in data
        assert "elections_inactives" in data
        assert data["total_elections"] >= 3
        assert data["elections_actives"] >= 2
        assert data["elections_inactives"] >= 1

        # Vérifier les stats par statut
        assert "statut_programmee" in data
        assert "statut_en_cours" in data
        assert "statut_terminee" in data

        # Vérifier les stats par type
        assert "type_presidentielle" in data
        assert "type_legislative" in data

    def test_api_pagination_limits(self, client):
        """Test des limites de pagination."""
        # Test avec limite trop grande
        response = client.get("/elections/?limit=101")
        assert response.status_code == 422

        # Test avec offset négatif
        response = client.get("/elections/?offset=-1")
        assert response.status_code == 422

    def test_comprehensive_election_workflow(self, client, test_db_session):
        """Test de workflow complet d'une élection."""
        future_date = date.today() + timedelta(days=30)

        # 1. Créer une élection
        election_data = {
            "type_election": "presidentielle",
            "nom_election": "Workflow Test Election",
            "description": "Test de workflow complet",
            "date_election": future_date.isoformat(),
            "statut": "programmee",
            "nombre_tours": 2,
            "tour_actuel": 1,
            "active": True
        }

        create_response = client.post("/elections/", json=election_data)
        assert create_response.status_code == 201
        election_id = create_response.json()["id_election"]

        # 2. Récupérer l'élection
        get_response = client.get(f"/elections/{election_id}")
        assert get_response.status_code == 200
        assert get_response.json()["statut"] == "programmee"

        # 3. Changer le statut à "en_cours"
        status_response = client.patch(f"/elections/{election_id}/statut?nouveau_statut=en_cours")
        assert status_response.status_code == 200
        assert status_response.json()["statut"] == "en_cours"

        # 4. Mettre à jour vers le deuxième tour
        update_data = {
            "type_election": "presidentielle",
            "nom_election": "Workflow Test Election",
            "description": "Test de workflow complet - Tour 2",
            "date_election": future_date.isoformat(),
            "statut": "en_cours",
            "nombre_tours": 2,
            "tour_actuel": 2,
            "active": True
        }

        update_response = client.put(f"/elections/{election_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["tour_actuel"] == 2

        # 5. Terminer l'élection
        final_status_response = client.patch(f"/elections/{election_id}/statut?nouveau_statut=terminee")
        assert final_status_response.status_code == 200
        assert final_status_response.json()["statut"] == "terminee"

        # 6. Vérifier dans la liste générale
        list_response = client.get("/elections/")
        assert list_response.status_code == 200
        elections = list_response.json()
        workflow_election = next((e for e in elections if e["id_election"] == election_id), None)
        assert workflow_election is not None
        assert workflow_election["est_terminee"] is True

        # 7. Supprimer l'élection
        delete_response = client.delete(f"/elections/{election_id}")
        assert delete_response.status_code == 200

        # 8. Vérifier la suppression
        final_get_response = client.get(f"/elections/{election_id}")
        assert final_get_response.status_code == 404