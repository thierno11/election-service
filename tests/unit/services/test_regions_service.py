import pytest
from unittest.mock import Mock
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from services.regions_services import create_region, get_all_region, update_region, delete_region
from model.region_model import Region
from model.departement_model import Departement
from schema.region_schema import RegionSchema

class TestRegionsService:

    def test_create_region_success(self, test_db_session):
        region_data = RegionSchema(nom_region="Nouvelle Région")

        result = create_region(region_data, test_db_session)

        assert result.nom_region == "Nouvelle Région"
        assert result.id_region is not None

        # Vérifier que la région a été ajoutée à la DB
        saved_region = test_db_session.query(Region).filter(Region.nom_region == "Nouvelle Région").first()
        assert saved_region is not None

    def test_create_region_duplicate_name(self, test_db_session):
        # Créer une région existante
        existing_region = Region(nom_region="Région Existante")
        test_db_session.add(existing_region)
        test_db_session.commit()

        # Essayer de créer une région avec le même nom
        region_data = RegionSchema(nom_region="Région Existante")

        with pytest.raises(HTTPException) as exc_info:
            create_region(region_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "existe déjà" in str(exc_info.value.detail)

    def test_get_all_region_empty(self, test_db_session):
        result = get_all_region(test_db_session)
        assert result == []

    def test_get_all_region_with_departments(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer des départements
        dept1 = Departement(nom_departement="Dept 1", id_region=region.id_region)
        dept2 = Departement(nom_departement="Dept 2", id_region=region.id_region)
        test_db_session.add_all([dept1, dept2])
        test_db_session.commit()

        result = get_all_region(test_db_session)

        assert len(result) == 1
        assert result[0].nom_region == "Test Région"
        assert result[0].nombre_departement == 2

    def test_update_region_success(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Ancienne Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Mettre à jour
        update_data = RegionSchema(nom_region="Nouvelle Région")
        result = update_region(region.id_region, update_data, test_db_session)

        assert result.nom_region == "Nouvelle Région"
        assert result.id_region == region.id_region

    def test_update_region_not_found(self, test_db_session):
        update_data = RegionSchema(nom_region="Test")

        with pytest.raises(HTTPException) as exc_info:
            update_region(999, update_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "introuvable" in str(exc_info.value.detail)

    def test_update_region_duplicate_name(self, test_db_session):
        # Créer deux régions
        region1 = Region(nom_region="Région 1")
        region2 = Region(nom_region="Région 2")
        test_db_session.add_all([region1, region2])
        test_db_session.commit()

        # Essayer de renommer region2 avec le nom de region1
        update_data = RegionSchema(nom_region="Région 1")

        with pytest.raises(HTTPException) as exc_info:
            update_region(region2.id_region, update_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "déjà utilisé" in str(exc_info.value.detail)

    def test_delete_region_success(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Région à supprimer")
        test_db_session.add(region)
        test_db_session.commit()
        region_id = region.id_region

        result = delete_region(region_id, test_db_session)

        assert "supprimée avec succès" in result["message"]

        # Vérifier que la région a été supprimée
        deleted_region = test_db_session.query(Region).filter(Region.id_region == region_id).first()
        assert deleted_region is None

    def test_delete_region_not_found(self, test_db_session):
        with pytest.raises(HTTPException) as exc_info:
            delete_region(999, test_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "introuvable" in str(exc_info.value.detail)