"""Tests pour le service des élections."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

from app.model.election_model import Election
from app.schema.election_schema import ElectionSchema, TypeElection, StatutElection
from app.services.elections_service import (
    create_election,
    get_all_elections,
    get_election_by_id,
    get_election_detail,
    update_election,
    delete_election,
    toggle_election_status,
    search_elections
)


class TestElectionsService:
    """Tests pour le service de gestion des élections."""

    def test_create_election_success(self, test_db_session):
        """Test de création d'une élection avec succès."""
        future_date = date.today() + timedelta(days=30)

        election_data = ElectionSchema(
            type_election=TypeElection.PRESIDENTIELLE,
            nom_election="Test Election",
            description="Test description",
            date_election=future_date,
            statut=StatutElection.PROGRAMMEE,
            nombre_tours=2,
            tour_actuel=1,
            active=True
        )

        result = create_election(election_data, test_db_session)

        assert result.id_election is not None
        assert result.nom_election == "Test Election"
        assert result.type_election == "presidentielle"
        assert result.date_election == future_date
        assert result.statut == "programmee"
        assert result.nombre_tours == 2
        assert result.tour_actuel == 1
        assert result.active is True

    def test_create_election_duplicate_name(self, test_db_session):
        """Test de création d'une élection avec nom existant."""
        future_date = date.today() + timedelta(days=30)

        # Créer la première élection
        election1 = Election(
            type_election="presidentielle",
            nom_election="Election Unique",
            date_election=future_date
        )
        test_db_session.add(election1)
        test_db_session.commit()

        # Tenter de créer une seconde élection avec le même nom
        election_data = ElectionSchema(
            type_election=TypeElection.LEGISLATIVE,
            nom_election="Election Unique",
            date_election=future_date
        )

        with pytest.raises(HTTPException) as exc_info:
            create_election(election_data, test_db_session)

        assert exc_info.value.status_code == 400
        assert "Election Unique" in str(exc_info.value.detail)

    def test_create_election_same_type_same_date(self, test_db_session):
        """Test de création d'une élection du même type à la même date."""
        future_date = date.today() + timedelta(days=40)

        # Créer la première élection
        election1 = Election(
            type_election="presidentielle",
            nom_election="Première Election",
            date_election=future_date,
            active=True
        )
        test_db_session.add(election1)
        test_db_session.commit()

        # Tenter de créer une seconde élection du même type à la même date
        election_data = ElectionSchema(
            type_election=TypeElection.PRESIDENTIELLE,
            nom_election="Deuxième Election",
            date_election=future_date
        )

        with pytest.raises(HTTPException) as exc_info:
            create_election(election_data, test_db_session)

        assert exc_info.value.status_code == 400
        assert "presidentielle" in str(exc_info.value.detail)

    def test_get_all_elections_success(self, test_db_session):
        """Test de récupération de toutes les élections."""
        future_date1 = date.today() + timedelta(days=10)
        future_date2 = date.today() + timedelta(days=20)

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
            active=True
        )

        test_db_session.add_all([election1, election2])
        test_db_session.commit()

        result = get_all_elections(test_db_session)

        assert len(result) == 2
        # Vérifier l'ordre (plus récentes d'abord)
        assert result[0].nom_election == "Election 2"
        assert result[1].nom_election == "Election 1"

    def test_get_all_elections_with_filters(self, test_db_session):
        """Test de récupération des élections avec filtres."""
        future_date = date.today() + timedelta(days=15)

        election1 = Election(
            type_election="presidentielle",
            nom_election="Election Présidentielle",
            date_election=future_date,
            statut="programmee",
            active=True
        )

        election2 = Election(
            type_election="legislative",
            nom_election="Election Législative",
            date_election=future_date,
            statut="en_cours",
            active=True
        )

        election3 = Election(
            type_election="presidentielle",
            nom_election="Election Inactive",
            date_election=future_date,
            active=False
        )

        test_db_session.add_all([election1, election2, election3])
        test_db_session.commit()

        # Test filtre par type
        result_type = get_all_elections(
            test_db_session,
            type_election="presidentielle"
        )
        assert len(result_type) == 1
        assert result_type[0].nom_election == "Election Présidentielle"

        # Test filtre par statut
        result_statut = get_all_elections(
            test_db_session,
            statut="en_cours"
        )
        assert len(result_statut) == 1
        assert result_statut[0].nom_election == "Election Législative"

        # Test filtre active_only=False
        result_all = get_all_elections(
            test_db_session,
            active_only=False
        )
        assert len(result_all) == 3

    def test_get_election_by_id_success(self, test_db_session):
        """Test de récupération d'une élection par ID."""
        future_date = date.today() + timedelta(days=25)

        election = Election(
            type_election="locale",
            nom_election="Election Test",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()

        result = get_election_by_id(election.id_election, test_db_session)

        assert result is not None
        assert result.id_election == election.id_election
        assert result.nom_election == "Election Test"

    def test_get_election_by_id_not_found(self, test_db_session):
        """Test de récupération d'une élection inexistante."""
        result = get_election_by_id(9999, test_db_session)
        assert result is None

    def test_get_election_detail_success(self, test_db_session):
        """Test de récupération des détails d'une élection."""
        future_date = date.today() + timedelta(days=35)

        election = Election(
            type_election="communale",
            nom_election="Election Détaillée",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()

        result = get_election_detail(election.id_election, test_db_session)

        assert result.id_election == election.id_election
        assert result.nom_election == "Election Détaillée"
        assert result.nombre_resultats == 0
        assert result.nombre_participations == 0

    def test_get_election_detail_not_found(self, test_db_session):
        """Test de récupération des détails d'une élection inexistante."""
        with pytest.raises(HTTPException) as exc_info:
            get_election_detail(9999, test_db_session)

        assert exc_info.value.status_code == 404

    def test_update_election_success(self, test_db_session):
        """Test de mise à jour d'une élection."""
        future_date = date.today() + timedelta(days=45)

        election = Election(
            type_election="departementale",
            nom_election="Election Originale",
            date_election=future_date,
            nombre_tours=1
        )
        test_db_session.add(election)
        test_db_session.commit()

        new_date = date.today() + timedelta(days=50)
        update_data = ElectionSchema(
            type_election=TypeElection.DEPARTEMENTALE,
            nom_election="Election Modifiée",
            date_election=new_date,
            nombre_tours=2,
            tour_actuel=1
        )

        result = update_election(election.id_election, update_data, test_db_session)

        assert result.nom_election == "Election Modifiée"
        assert result.date_election == new_date
        assert result.nombre_tours == 2

    def test_update_election_not_found(self, test_db_session):
        """Test de mise à jour d'une élection inexistante."""
        future_date = date.today() + timedelta(days=30)

        update_data = ElectionSchema(
            type_election=TypeElection.PRESIDENTIELLE,
            nom_election="Election Inexistante",
            date_election=future_date
        )

        with pytest.raises(HTTPException) as exc_info:
            update_election(9999, update_data, test_db_session)

        assert exc_info.value.status_code == 404

    def test_update_election_duplicate_name(self, test_db_session):
        """Test de mise à jour avec un nom déjà existant."""
        future_date = date.today() + timedelta(days=30)

        election1 = Election(
            type_election="presidentielle",
            nom_election="Election 1",
            date_election=future_date
        )

        election2 = Election(
            type_election="legislative",
            nom_election="Election 2",
            date_election=future_date
        )

        test_db_session.add_all([election1, election2])
        test_db_session.commit()

        # Tenter de renommer election2 avec le nom de election1
        update_data = ElectionSchema(
            type_election=TypeElection.LEGISLATIVE,
            nom_election="Election 1",
            date_election=future_date
        )

        with pytest.raises(HTTPException) as exc_info:
            update_election(election2.id_election, update_data, test_db_session)

        assert exc_info.value.status_code == 400
        assert "Election 1" in str(exc_info.value.detail)

    def test_update_election_invalid_tour(self, test_db_session):
        """Test de mise à jour avec tour actuel invalide."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="presidentielle",
            nom_election="Election Tour",
            date_election=future_date,
            nombre_tours=2
        )
        test_db_session.add(election)
        test_db_session.commit()

        # Tenter de mettre tour_actuel > nombre_tours
        update_data = ElectionSchema(
            type_election=TypeElection.PRESIDENTIELLE,
            nom_election="Election Tour",
            date_election=future_date,
            nombre_tours=2,
            tour_actuel=3  # Invalid
        )

        with pytest.raises(HTTPException) as exc_info:
            update_election(election.id_election, update_data, test_db_session)

        assert exc_info.value.status_code == 400
        assert "tour actuel" in str(exc_info.value.detail)

    def test_delete_election_success(self, test_db_session):
        """Test de suppression d'une élection."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="regionale",
            nom_election="Election à Supprimer",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()
        election_id = election.id_election

        result = delete_election(election_id, test_db_session)

        assert "Election à Supprimer" in result["message"]
        assert "supprimée avec succès" in result["message"]

        # Vérifier que l'élection n'existe plus
        deleted_election = get_election_by_id(election_id, test_db_session)
        assert deleted_election is None

    def test_delete_election_not_found(self, test_db_session):
        """Test de suppression d'une élection inexistante."""
        with pytest.raises(HTTPException) as exc_info:
            delete_election(9999, test_db_session)

        assert exc_info.value.status_code == 404

    def test_toggle_election_status_success(self, test_db_session):
        """Test de changement de statut d'une élection."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="referendum",
            nom_election="Election Statut",
            date_election=future_date,
            statut="programmee"
        )
        test_db_session.add(election)
        test_db_session.commit()

        result = toggle_election_status(election.id_election, "en_cours", test_db_session)

        assert result.statut == "en_cours"

    def test_toggle_election_status_invalid(self, test_db_session):
        """Test de changement de statut avec statut invalide."""
        future_date = date.today() + timedelta(days=30)

        election = Election(
            type_election="presidentielle",
            nom_election="Election Statut Invalid",
            date_election=future_date
        )
        test_db_session.add(election)
        test_db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            toggle_election_status(election.id_election, "statut_invalide", test_db_session)

        assert exc_info.value.status_code == 400
        assert "Statut invalide" in str(exc_info.value.detail)

    def test_search_elections_success(self, test_db_session):
        """Test de recherche d'élections."""
        future_date = date.today() + timedelta(days=30)

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

        election3 = Election(
            type_election="locale",
            nom_election="Election Municipale",
            description="Election locale",
            date_election=future_date,
            active=False  # Inactive, ne doit pas apparaître
        )

        test_db_session.add_all([election1, election2, election3])
        test_db_session.commit()

        # Recherche par nom
        result_nom = search_elections("présidentielle", test_db_session)
        assert len(result_nom) == 1
        assert result_nom[0].nom_election == "Élection Présidentielle 2024"

        # Recherche par type
        result_type = search_elections("legislative", test_db_session)
        assert len(result_type) == 1
        assert result_type[0].type_election == "legislative"

        # Recherche par description
        result_desc = search_elections("parlement", test_db_session)
        assert len(result_desc) == 1
        assert result_desc[0].nom_election == "Élections Législatives"

        # Recherche sans résultat
        result_empty = search_elections("inexistant", test_db_session)
        assert len(result_empty) == 0

    def test_search_elections_with_limit(self, test_db_session):
        """Test de recherche d'élections avec limite."""
        future_date = date.today() + timedelta(days=30)

        # Créer plusieurs élections avec le même terme
        for i in range(5):
            election = Election(
                type_election="locale",
                nom_election=f"Election Locale {i+1}",
                date_election=future_date,
                active=True
            )
            test_db_session.add(election)

        test_db_session.commit()

        result = search_elections("locale", test_db_session, limit=3)
        assert len(result) == 3

    def test_create_election_database_error(self, test_db_session):
        """Test de gestion d'erreur de base de données lors de la création."""
        # Mock pour simuler une erreur SQLAlchemy
        test_db_session.commit = Mock(side_effect=SQLAlchemyError("Database error"))

        future_date = date.today() + timedelta(days=30)
        election_data = ElectionSchema(
            type_election=TypeElection.PRESIDENTIELLE,
            nom_election="Election Error",
            date_election=future_date
        )

        with pytest.raises(HTTPException) as exc_info:
            create_election(election_data, test_db_session)

        assert exc_info.value.status_code == 500