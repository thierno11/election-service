import pytest
from sqlalchemy.exc import IntegrityError
from model.region_model import Region
from model.departement_model import Departement

class TestDepartementModel:
    def test_create_departement(self, test_db_session):
        region = Region(nom_region="Dakar")
        test_db_session.add(region)
        test_db_session.commit()

        departement = Departement(
            nom_departement="Dakar",
            id_region=region.id_region
        )
        test_db_session.add(departement)
        test_db_session.commit()

        assert departement.id_departement is not None
        assert departement.nom_departement == "Dakar"
        assert departement.id_region == region.id_region

    def test_departement_unique_constraint(self, test_db_session):
        region = Region(nom_region="Thiès")
        test_db_session.add(region)
        test_db_session.commit()

        dept1 = Departement(nom_departement="Thiès", id_region=region.id_region)
        dept2 = Departement(nom_departement="Thiès", id_region=region.id_region)

        test_db_session.add(dept1)
        test_db_session.commit()

        test_db_session.add(dept2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_departement_foreign_key_constraint(self, test_db_session):
        departement = Departement(
            nom_departement="Test",
            id_region=999  # Non-existent region
        )
        test_db_session.add(departement)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_departement_required_fields(self, test_db_session):
        region = Region(nom_region="Test Region")
        test_db_session.add(region)
        test_db_session.commit()

        # Test missing nom_departement
        dept1 = Departement(nom_departement=None, id_region=region.id_region)
        test_db_session.add(dept1)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

        test_db_session.rollback()

        # Test missing id_region
        dept2 = Departement(nom_departement="Test Dept", id_region=None)
        test_db_session.add(dept2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()