"""Tests pour le modèle Election."""

import pytest
from sqlalchemy.exc import IntegrityError
from model.election_model import Election


class TestElectionModel:

    def test_create_election(self, test_db_session):
        """Test de création d'une élection."""
        election = Election(
            type_election="presidentielle"
        )

        test_db_session.add(election)
        test_db_session.commit()

        assert election.id_election is not None
        assert election.type_election == "presidentielle"

    def test_election_required_fields(self, test_db_session):
        """Test des champs obligatoires."""
        # Test sans type_election
        election = Election()

        test_db_session.add(election)
        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_multiple_elections(self, test_db_session):
        """Test de création de plusieurs élections."""
        election1 = Election(type_election="presidentielle")
        election2 = Election(type_election="legislative")

        test_db_session.add_all([election1, election2])
        test_db_session.commit()

        assert election1.id_election != election2.id_election
        assert election1.type_election == "presidentielle"
        assert election2.type_election == "legislative"