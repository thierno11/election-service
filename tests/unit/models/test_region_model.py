import pytest
from sqlalchemy.exc import IntegrityError
from model.region_model import Region

class TestRegionModel:
    def test_create_region(self, test_db_session):
        region = Region(nom_region="Dakar")
        test_db_session.add(region)
        test_db_session.commit()

        assert region.id_region is not None
        assert region.nom_region == "Dakar"

    def test_region_unique_constraint(self, test_db_session):
        region1 = Region(nom_region="Thiès")
        region2 = Region(nom_region="Thiès")


        test_db_session.add(region1)
        test_db_session.commit()

        test_db_session.add(region2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_region_required_fields(self, test_db_session):
        region = Region(nom_region=None)
        test_db_session.add(region)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_region_string_representation(self, test_db_session):
        region = Region(nom_region="Saint-Louis")
        test_db_session.add(region)
        test_db_session.commit()

        assert region.nom_region == "Saint-Louis"
        assert region.id_region is not None