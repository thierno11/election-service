import pytest
from sqlalchemy.exc import IntegrityError
from model.region_model import Region
from model.departement_model import Departement
from model.commune_model import Commune
from model.bureau_vote import BureauVote

class TestBureauVoteModel:
    def test_create_bureau_vote(self, test_db_session):
        # Create dependencies
        region = Region(nom_region="Dakar")
        test_db_session.add(region)
        test_db_session.commit()

        departement = Departement(nom_departement="Dakar", id_region=region.id_region)
        test_db_session.add(departement)
        test_db_session.commit()

        commune = Commune(nom_commune="Commune Test", id_departement=departement.id_departement)
        test_db_session.add(commune)
        test_db_session.commit()

        # Create bureau vote
        bureau = BureauVote(
            nom_centre="École Primaire",
            numero_bureau=1,
            implantation="Quartier Nord",
            id_commune=commune.id_commune
        )
        test_db_session.add(bureau)
        test_db_session.commit()

        assert bureau.id_bureau is not None
        assert bureau.nom_centre == "École Primaire"
        assert bureau.numero_bureau == 1
        assert bureau.implantation == "Quartier Nord"
        assert bureau.id_commune == commune.id_commune

    def test_bureau_vote_unique_constraint(self, test_db_session):
        # Create dependencies
        region = Region(nom_region="Thiès")
        test_db_session.add(region)
        test_db_session.commit()

        departement = Departement(nom_departement="Thiès", id_region=region.id_region)
        test_db_session.add(departement)
        test_db_session.commit()

        commune = Commune(nom_commune="Commune Test", id_departement=departement.id_departement)
        test_db_session.add(commune)
        test_db_session.commit()

        # Create first bureau
        bureau1 = BureauVote(
            nom_centre="École Test",
            numero_bureau=1,
            implantation="Quartier A",
            id_commune=commune.id_commune
        )
        test_db_session.add(bureau1)
        test_db_session.commit()

        # Try to create duplicate bureau (same nom_centre, id_commune, numero_bureau)
        bureau2 = BureauVote(
            nom_centre="École Test",
            numero_bureau=1,
            implantation="Quartier B",
            id_commune=commune.id_commune
        )
        test_db_session.add(bureau2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_bureau_vote_required_fields(self, test_db_session):
        # Create commune dependency
        region = Region(nom_region="Test Region")
        test_db_session.add(region)
        test_db_session.commit()

        departement = Departement(nom_departement="Test Dept", id_region=region.id_region)
        test_db_session.add(departement)
        test_db_session.commit()

        commune = Commune(nom_commune="Test Commune", id_departement=departement.id_departement)
        test_db_session.add(commune)
        test_db_session.commit()

        # Test missing nom_centre
        bureau1 = BureauVote(
            nom_centre=None,
            numero_bureau=1,
            implantation="Test",
            id_commune=commune.id_commune
        )
        test_db_session.add(bureau1)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

        test_db_session.rollback()

        # Test missing numero_bureau
        bureau2 = BureauVote(
            nom_centre="Test Centre",
            numero_bureau=None,
            implantation="Test",
            id_commune=commune.id_commune
        )
        test_db_session.add(bureau2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_bureau_vote_foreign_key_constraint(self, test_db_session):
        bureau = BureauVote(
            nom_centre="Test Centre",
            numero_bureau=1,
            implantation="Test",
            id_commune=999  # Non-existent commune
        )
        test_db_session.add(bureau)

        with pytest.raises(IntegrityError):
            test_db_session.commit()