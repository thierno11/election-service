import pytest
from fastapi import HTTPException, status
from app.services.departements_service import create_departement, get_all_departement, update_departement, delete_departement
from app.model.region_model import Region
from app.model.departement_model import Departement
from app.model.commune_model import Commune
from app.schema.departement_schema import DepartementSchema

class TestDepartementsService:

    def test_create_departement_success(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        dept_data = DepartementSchema(nom_departement="Nouveau Département", id_region=region.id_region)

        result = create_departement(dept_data, test_db_session)

        assert result.nom_departement == "Nouveau Département"
        assert result.id_region == region.id_region
        assert result.id_departement is not None

    def test_create_departement_duplicate_in_same_region(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département existant
        existing_dept = Departement(nom_departement="Département Existant", id_region=region.id_region)
        test_db_session.add(existing_dept)
        test_db_session.commit()

        # Essayer de créer un département avec le même nom dans la même région
        dept_data = DepartementSchema(nom_departement="Département Existant", id_region=region.id_region)

        with pytest.raises(HTTPException) as exc_info:
            create_departement(dept_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "existe déjà" in str(exc_info.value.detail)

    def test_create_departement_same_name_different_region(self, test_db_session):
        # Créer deux régions
        region1 = Region(nom_region="Région 1")
        region2 = Region(nom_region="Région 2")
        test_db_session.add_all([region1, region2])
        test_db_session.commit()

        # Créer un département dans la première région
        dept1 = Departement(nom_departement="Même Nom", id_region=region1.id_region)
        test_db_session.add(dept1)
        test_db_session.commit()

        # Créer un département avec le même nom dans une autre région (devrait réussir)
        dept_data = DepartementSchema(nom_departement="Même Nom", id_region=region2.id_region)

        result = create_departement(dept_data, test_db_session)

        assert result.nom_departement == "Même Nom"
        assert result.id_region == region2.id_region

    def test_get_all_departement_empty(self, test_db_session):
        result = get_all_departement(test_db_session)
        assert result == []

    def test_get_all_departement_with_communes(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        dept = Departement(nom_departement="Test Département", id_region=region.id_region)
        test_db_session.add(dept)
        test_db_session.commit()

        # Créer des communes
        commune1 = Commune(nom_commune="Commune 1", id_departement=dept.id_departement)
        commune2 = Commune(nom_commune="Commune 2", id_departement=dept.id_departement)
        test_db_session.add_all([commune1, commune2])
        test_db_session.commit()

        result = get_all_departement(test_db_session)

        assert len(result) == 1
        assert result[0].nom_departement == "Test Département"
        assert result[0].nombre_commune == 2

    def test_update_departement_success(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        dept = Departement(nom_departement="Ancien Nom", id_region=region.id_region)
        test_db_session.add(dept)
        test_db_session.commit()

        # Mettre à jour
        update_data = DepartementSchema(nom_departement="Nouveau Nom", id_region=region.id_region)
        result = update_departement(dept.id_departement, update_data, test_db_session)

        assert result.nom_departement == "Nouveau Nom"
        assert result.id_departement == dept.id_departement

    def test_update_departement_not_found(self, test_db_session):
        # Créer une région pour les données valides
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        update_data = DepartementSchema(nom_departement="Test", id_region=region.id_region)

        with pytest.raises(HTTPException) as exc_info:
            update_departement(999, update_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "introuvable" in str(exc_info.value.detail)

    def test_update_departement_duplicate_name(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer deux départements
        dept1 = Departement(nom_departement="Département 1", id_region=region.id_region)
        dept2 = Departement(nom_departement="Département 2", id_region=region.id_region)
        test_db_session.add_all([dept1, dept2])
        test_db_session.commit()

        # Essayer de renommer dept2 avec le nom de dept1
        update_data = DepartementSchema(nom_departement="Département 1", id_region=region.id_region)

        with pytest.raises(HTTPException) as exc_info:
            update_departement(dept2.id_departement, update_data, test_db_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "déjà utilisé" in str(exc_info.value.detail)

    def test_delete_departement_success(self, test_db_session):
        # Créer une région
        region = Region(nom_region="Test Région")
        test_db_session.add(region)
        test_db_session.commit()

        # Créer un département
        dept = Departement(nom_departement="Département à supprimer", id_region=region.id_region)
        test_db_session.add(dept)
        test_db_session.commit()
        dept_id = dept.id_departement

        result = delete_departement(dept_id, test_db_session)

        assert "supprimé avec succès" in result["message"]

        # Vérifier que le département a été supprimé
        deleted_dept = test_db_session.query(Departement).filter(Departement.id_departement == dept_id).first()
        assert deleted_dept is None

    def test_delete_departement_not_found(self, test_db_session):
        with pytest.raises(HTTPException) as exc_info:
            delete_departement(999, test_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "introuvable" in str(exc_info.value.detail)