from model.region_model import Region

class TestRegionsAPI:

    def test_create_region_success(self, client):
        region_data = {"nom_region": "Nouvelle Région API"}

        response = client.post("/regions/", json=region_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nom_region"] == "Nouvelle Région API"
        assert "id_region" in data

    def test_create_region_duplicate(self, client):
        # Créer une région
        region_data = {"nom_region": "Région Dupliquée"}
        client.post("/regions/", json=region_data)

        # Essayer de créer la même région
        response = client.post("/regions/", json=region_data)

        assert response.status_code == 400
        assert "existe déjà" in response.json()["detail"]

    def test_create_region_invalid_data(self, client):
        # Test avec des données manquantes
        response = client.post("/regions/", json={})

        assert response.status_code == 422  # Validation error

    def test_get_all_regions_empty(self, client):
        response = client.get("/regions/")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_regions_with_data(self, client, test_db_session):
        # Créer des régions directement en base
        region1 = Region(nom_region="Région 1")
        region2 = Region(nom_region="Région 2")
        test_db_session.add_all([region1, region2])
        test_db_session.commit()

        response = client.get("/regions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(r["nom_region"] == "Région 1" for r in data)
        assert any(r["nom_region"] == "Région 2" for r in data)

    def test_update_region_success(self, client):
        # Créer une région
        create_response = client.post("/regions/", json={"nom_region": "Ancienne Région"})
        region_id = create_response.json()["id_region"]

        # Mettre à jour
        update_data = {"nom_region": "Nouvelle Région"}
        response = client.put(f"/regions/{region_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nom_region"] == "Nouvelle Région"
        assert data["id_region"] == region_id

    def test_update_region_not_found(self, client):
        update_data = {"nom_region": "Test"}
        response = client.put("/regions/999", json=update_data)

        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]

    def test_update_region_duplicate_name(self, client):
        # Créer deux régions
        client.post("/regions/", json={"nom_region": "Région A"})
        create_response = client.post("/regions/", json={"nom_region": "Région B"})
        region_b_id = create_response.json()["id_region"]

        # Essayer de renommer Région B avec le nom de Région A
        update_data = {"nom_region": "Région A"}
        response = client.put(f"/regions/{region_b_id}", json=update_data)

        assert response.status_code == 400
        assert "déjà utilisé" in response.json()["detail"]

    def test_delete_region_success(self, client):
        # Créer une région
        create_response = client.post("/regions/", json={"nom_region": "Région à supprimer"})
        region_id = create_response.json()["id_region"]

        # Supprimer
        response = client.delete(f"/regions/{region_id}")

        assert response.status_code == 204

        # Vérifier que la région n'existe plus
        get_response = client.get("/regions/")
        regions = get_response.json()
        assert not any(r["id_region"] == region_id for r in regions)

    def test_delete_region_not_found(self, client):
        response = client.delete("/regions/999")

        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]

    def test_region_workflow_complete(self, client):
        # Test d'un workflow complet

        # 1. Créer une région
        create_data = {"nom_region": "Workflow Région"}
        create_response = client.post("/regions/", json=create_data)
        assert create_response.status_code == 200
        region_id = create_response.json()["id_region"]

        # 2. Vérifier qu'elle apparaît dans la liste
        list_response = client.get("/regions/")
        assert any(r["id_region"] == region_id for r in list_response.json())

        # 3. Mettre à jour
        update_data = {"nom_region": "Workflow Région Modifiée"}
        update_response = client.put(f"/regions/{region_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["nom_region"] == "Workflow Région Modifiée"

        # 4. Supprimer
        delete_response = client.delete(f"/regions/{region_id}")
        assert delete_response.status_code == 204

        # 5. Vérifier qu'elle a disparu
        final_list = client.get("/regions/")
        assert not any(r["id_region"] == region_id for r in final_list.json())