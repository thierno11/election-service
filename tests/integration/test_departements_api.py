import pytest
from model.region_model import Region
from model.departement_model import Departement

class TestDepartementsAPI:

    def test_create_departement_success(self, client, test_db_session):
        # Créer une région d'abord
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        dept_data = {
            "nom_departement": "Nouveau Département",
            "id_region": region.id_region
        }

        response = client.post("/departements/", json=dept_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nom_departement"] == "Nouveau Département"
        assert data["id_region"] == region.id_region
        assert "id_departement" in data

    def test_create_departement_invalid_region(self, client):
        dept_data = {
            "nom_departement": "Test Département",
            "id_region": 999  # Région inexistante
        }

        response = client.post("/departements/", json=dept_data)

        assert response.status_code == 500  # Foreign key constraint violation

    def test_create_departement_duplicate_in_region(self, client, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        dept_data = {
            "nom_departement": "Département Dupliqué",
            "id_region": region.id_region
        }
        client.post("/departements/", json=dept_data)

        # Essayer de créer le même département dans la même région
        response = client.post("/departements/", json=dept_data)

        assert response.status_code == 400
        assert "existe déjà" in response.json()["detail"]

    def test_create_departement_same_name_different_regions(self, client, test_db_session):
        # Créer deux régions
        region1 = Region(nom_region="Région 1")
        region2 = Region(nom_region="Région 2")
        test_db_session.add_all([region1, region2])
        test_db_session.commit()

        # Créer un département dans la première région
        dept_data1 = {
            "nom_departement": "Même Nom",
            "id_region": region1.id_region
        }
        response1 = client.post("/departements/", json=dept_data1)
        assert response1.status_code == 200

        # Créer un département avec le même nom dans la deuxième région
        dept_data2 = {
            "nom_departement": "Même Nom",
            "id_region": region2.id_region
        }
        response2 = client.post("/departements/", json=dept_data2)
        assert response2.status_code == 200

    def test_get_all_departements_empty(self, client):
        response = client.get("/departements/")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_departements_with_data(self, client, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer des départements
        dept1 = Departement(nom_departement="Département 1", id_region=region.id_region)
        dept2 = Departement(nom_departement="Département 2", id_region=region.id_region)
        test_db_session.add_all([dept1, dept2])
        test_db_session.commit()

        response = client.get("/departements/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_departement_success(self, client, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        create_data = {
            "nom_departement": "Ancien Nom",
            "id_region": region.id_region
        }
        create_response = client.post("/departements/", json=create_data)
        dept_id = create_response.json()["id_departement"]

        # Mettre à jour
        update_data = {
            "nom_departement": "Nouveau Nom",
            "id_region": region.id_region
        }
        response = client.put(f"/departements/{dept_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nom_departement"] == "Nouveau Nom"
        assert data["id_departement"] == dept_id

    def test_update_departement_not_found(self, client, test_db_session):
        # Créer une région pour avoir des données valides
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        update_data = {
            "nom_departement": "Test",
            "id_region": region.id_region
        }
        response = client.put("/departements/999", json=update_data)

        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]

    def test_delete_departement_success(self, client, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        create_data = {
            "nom_departement": "Département à supprimer",
            "id_region": region.id_region
        }
        create_response = client.post("/departements/", json=create_data)
        dept_id = create_response.json()["id_departement"]

        # Supprimer
        response = client.delete(f"/departements/{dept_id}")

        assert response.status_code == 200
        assert "supprimé avec succès" in response.json()["message"]

    def test_delete_departement_not_found(self, client):
        response = client.delete("/departements/999")

        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]

    def test_departement_workflow_complete(self, client, test_db_session):
        # Créer une région
        region = Region(nom_region="Workflow Région")
        test_db_session.add(region)
        test_db_session.commit()

        # 1. Créer un département
        create_data = {
            "nom_departement": "Workflow Département",
            "id_region": region.id_region
        }
        create_response = client.post("/departements/", json=create_data)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id_departement"]

        # 2. Vérifier qu'il apparaît dans la liste
        list_response = client.get("/departements/")
        assert any(d["id_departement"] == dept_id for d in list_response.json())

        # 3. Mettre à jour
        update_data = {
            "nom_departement": "Workflow Département Modifié",
            "id_region": region.id_region
        }
        update_response = client.put(f"/departements/{dept_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["nom_departement"] == "Workflow Département Modifié"

        # 4. Supprimer
        delete_response = client.delete(f"/departements/{dept_id}")
        assert delete_response.status_code == 200

        # 5. Vérifier qu'il a disparu (en interrogeant la base directement)
        deleted_dept = test_db_session.query(Departement).filter(Departement.id_departement == dept_id).first()
        assert deleted_dept is None