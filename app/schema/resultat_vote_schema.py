"""Schémas Pydantic pour les résultats de vote."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResultatVoteSchema(BaseModel):
    """
    Schéma pour la création d'un résultat de vote.

    Attributes:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau de vote
        nom_candidat: Nom du candidat
        date_election: Date de l'élection
        voix: Nombre de voix
    """
    model_config = ConfigDict(from_attributes=True)

    id_election: int = Field(
        ...,
        description="Identifiant de l'élection",
        examples=[1]
    )

    id_bureau: int = Field(
        ...,
        description="Identifiant du bureau de vote",
        examples=[1]
    )

    nom_candidat: str = Field(
        ...,
        description="Nom du candidat",
        examples=["MACKY SALL"]
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection",
        examples=["2024-12-31"]
    )

    voix: int = Field(
        default=0,
        ge=0,
        description="Nombre de voix"
    )

    @field_validator("nom_candidat")
    @classmethod
    def to_upper(cls, value: str) -> str:
        """Convertit en majuscules."""
        if value:
            return value.upper()
        return value


class ResultatVoteBulkItem(BaseModel):
    """
    Schéma pour un item de création en masse.

    Attributes:
        nom_candidat: Nom du candidat
        voix: Nombre de voix
    """
    nom_candidat: str = Field(
        ...,
        description="Nom du candidat",
        examples=["MACKY SALL"]
    )

    voix: int = Field(
        default=0,
        ge=0,
        description="Nombre de voix"
    )

    @field_validator("nom_candidat")
    @classmethod
    def to_upper(cls, value: str) -> str:
        """Convertit en majuscules."""
        if value:
            return value.upper()
        return value


class ResultatVoteBulkSchema(BaseModel):
    """
    Schéma pour la création en masse de résultats de vote.

    Attributes:
        type_election: Type de l'élection
        id_bureau: Identifiant du bureau de vote
        date_election: Date de l'élection
        resultats: Liste des résultats (candidat + voix)
    """
    model_config = ConfigDict(from_attributes=True)
    commune: str =  Field(
        ...,
        description="Commune",
        examples=["PRESIDENTIELLE"]
    )
    
    centre: str =  Field(
        ...,
        description="Commune",
        examples=["PRESIDENTIELLE"]
    )

    type_election: str = Field(
        ...,
        description="Type de l'élection",
        examples=["PRESIDENTIELLE"]
    )

    bureau: int = Field(
        ...,
        description="numero bureau de vote",
        examples=[1]
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection",
        examples=["2024-12-31"]
    )

    resultats: List[ResultatVoteBulkItem] = Field(
        ...,
        description="Liste des résultats (candidat + voix)"
    )


class ResultatVoteReponse(BaseModel):
    """
    Schéma de réponse pour un résultat de vote.

    Attributes:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau de vote
        id_candidat: Identifiant du candidat
        date_election: Date de l'élection
        voix: Nombre de voix
    """
    model_config = ConfigDict(from_attributes=True)

    id_election: int = Field(
        ...,
        description="Identifiant de l'élection"
    )

    id_bureau: int = Field(
        ...,
        description="Identifiant du bureau de vote"
    )

    id_candidat: int = Field(
        ...,
        description="Identifiant du candidat"
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection"
    )

    voix: int = Field(
        ...,
        description="Nombre de voix"
    )


class StatistiquesResultat(BaseModel):
    """
    Schéma pour les statistiques de résultats d'un candidat agrégées.

    Attributes:
        niveau: Niveau géographique (bureau, centre, commune, departement, region, national)
        identifiant: Identifiant de l'entité (optionnel pour niveau national)
        nom: Nom de l'entité
        nom_candidat: Nom du candidat
        total_voix: Nombre total de voix pour ce candidat
        pourcentage: Pourcentage des voix par rapport au total des voix
        nombre_bureaux: Nombre de bureaux où ce candidat a obtenu des voix
    """
    model_config = ConfigDict(from_attributes=True)


    nom_candidat: str = Field(
        ...,
        description="Nom du candidat"
    )

    total_voix: int = Field(
        ...,
        ge=0,
        description="Nombre total de voix pour ce candidat"
    )

    pourcentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Pourcentage des voix par rapport au total"
    )


class StatistiquesResultatGlobal(BaseModel):
    """
    Schéma pour les statistiques globales d'une entité géographique.

    Attributes:
        niveau: Niveau géographique
        identifiant: Identifiant de l'entité
        nom: Nom de l'entité
        total_voix_global: Total des voix exprimées dans cette entité
        nombre_candidats: Nombre de candidats ayant obtenu des voix
        nombre_bureaux_total: Nombre total de bureaux dans cette entité
        resultats_candidats: Liste des résultats par candidat
    """
    model_config = ConfigDict(from_attributes=True)


    total_voix_global: int = Field(
        ...,
        ge=0,
        description="Total des voix exprimées dans cette entité"
    )

    resultats_candidats: List[StatistiquesResultat] = Field(
        ...,
        description="Liste des résultats par candidat"
    )


class StatistiquesResultatListe(BaseModel):
    """
    Schéma pour une liste de statistiques de résultats avec métadonnées.

    Attributes:
        type_election: Type d'élection
        date_election: Date de l'élection
        niveau: Niveau géographique des statistiques
        total_elements: Nombre total d'éléments dans la liste
        statistiques: Liste des statistiques globales par entité
    """
    model_config = ConfigDict(from_attributes=True)

    
    statistiques: StatistiquesResultatGlobal = Field(
        ...,
        description="Liste des statistiques de résultats par entité"
    )


class EvolutionVotesTemporelle(BaseModel):
    """
    Schéma pour l'évolution temporelle des votes par intervalle de 15 minutes.

    Attributes:
        heure_debut: Début de l'intervalle de 15 minutes
        heure_fin: Fin de l'intervalle de 15 minutes
        nombre_votes: Nombre de votes ajoutés dans cet intervalle
        cumul_votes: Nombre cumulé de votes jusqu'à cet intervalle
        pourcentage_cumul: Pourcentage cumulé par rapport au total
        votes_par_candidat: Détail des votes par candidat dans cet intervalle
    """
    model_config = ConfigDict(from_attributes=True)

    heure_debut: datetime = Field(
        ...,
        description="Début de l'intervalle de 15 minutes"
    )

    heure_fin: datetime = Field(
        ...,
        description="Fin de l'intervalle de 15 minutes"
    )

    nombre_votes: int = Field(
        ...,
        ge=0,
        description="Nombre de votes ajoutés dans cet intervalle"
    )

    cumul_votes: int = Field(
        ...,
        ge=0,
        description="Nombre cumulé de votes jusqu'à cet intervalle"
    )

    pourcentage_cumul: float = Field(
        ...,
        ge=0,
        le=100,
        description="Pourcentage cumulé par rapport au total"
    )

    votes_par_candidat: List[StatistiquesResultat] = Field(
        ...,
        description="Détail des votes par candidat dans cet intervalle"
    )


class EvolutionVotesTemporelleListe(BaseModel):
    """
    Schéma pour une liste d'évolutions temporelles des votes.
    """
    model_config = ConfigDict(from_attributes=True)

    id_election: int = Field(
        ...,
        description="Identifiant de l'élection"
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection"
    )

    total_votes: int = Field(
        ...,
        ge=0,
        description="Nombre total de votes"
    )

    duree_totale_minutes: int = Field(
        ...,
        ge=0,
        description="Durée totale en minutes entre le premier et dernier vote"
    )

    nombre_intervalles: int = Field(
        ...,
        ge=0,
        description="Nombre d'intervalles de 15 minutes"
    )

    evolution: List[EvolutionVotesTemporelle] = Field(
        ...,
        description="Liste des évolutions par intervalle de 15 minutes"
    )


class RepartitionGeographique(BaseModel):
    """
    Schéma pour la répartition géographique des votants et des votes.

    Attributes:
        identifiant: Identifiant de l'entité géographique
        nom: Nom de l'entité géographique
        total_electeurs: Nombre d'électeurs inscrits
        total_votants: Nombre de votants
        taux_participation: Taux de participation pour cette entité
        total_voix: Total des voix exprimées dans cette entité
        resultats_candidats: Résultats par candidat dans cette entité
    """
    model_config = ConfigDict(from_attributes=True)


    total_electeurs: int = Field(
        ...,
        ge=0,
        description="Nombre d'électeurs inscrits"
    )

    total_votants: int = Field(
        ...,
        ge=0,
        description="Nombre de votants"
    )

    taux_participation: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de participation pour cette entité"
    )

    total_voix: int = Field(
        ...,
        ge=0,
        description="Total des voix exprimées dans cette entité"
    )

    resultats_candidats: List[StatistiquesResultat] = Field(
        ...,
        description="Résultats par candidat dans cette entité"
    )


class StatistiquesGlobales(BaseModel):
    """
    Schéma pour les statistiques globales d'une élection (participation + résultats).

    Attributes:
        type_election: Type d'élection
        date_election: Date de l'élection
        niveau: Niveau géographique
        identifiant: Identifiant de l'entité
        nom: Nom de l'entité

        # Données de participation
        total_electeurs: Nombre total d'électeurs inscrits
        total_votants: Nombre total de votants
        total_bulletins_nuls: Nombre total de bulletins nuls
        total_suffrages: Nombre total de suffrages exprimés
        taux_participation: Taux de participation en pourcentage

        # Données de résultats
        total_voix_comptabilisees: Total des voix comptabilisées par candidat
        nombre_candidats: Nombre de candidats
        nombre_bureaux: Nombre de bureaux concernés

        # Résultats par candidat
        resultats_candidats: Liste des résultats détaillés par candidat
    """
    model_config = ConfigDict(from_attributes=True)

    # Données de participation
    total_electeurs: int = Field(
        ...,
        ge=0,
        description="Nombre total d'électeurs inscrits"
    )

    total_votants: int = Field(
        ...,
        ge=0,
        description="Nombre total de votants"
    )

    total_bulletins_nuls: int = Field(
        ...,
        ge=0,
        description="Nombre total de bulletins nuls"
    )

    total_suffrages: int = Field(
        ...,
        ge=0,
        description="Nombre total de suffrages exprimés"
    )

    taux_participation: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de participation en pourcentage"
    )

    # Données de résultats
    total_voix_comptabilisees: int = Field(
        ...,
        ge=0,
        description="Total des voix comptabilisées par candidat"
    )

    nombre_candidats: int = Field(
        ...,
        ge=0,
        description="Nombre de candidats"
    )

    nombre_bureaux: int = Field(
        ...,
        ge=0,
        description="Nombre de bureaux concernés"
    )

    # Cohérence des données
    coherence_voix_suffrages: bool = Field(
        ...,
        description="Indique si le total des voix par candidat correspond aux suffrages exprimés"
    )

    ecart_voix_suffrages: int = Field(
        ...,
        description="Écart entre le total des voix par candidat et les suffrages exprimés"
    )

    # Résultats détaillés
    resultats_candidats: List[StatistiquesResultat] = Field(
        ...,
        description="Liste des résultats détaillés par candidat"
    )

    # Répartition géographique
    repartition_geographique: List[RepartitionGeographique] = Field(
        ...,
        description="Répartition géographique des votants (par région si national, par département si région)"
    )


class StatistiquesGlobalesListe(BaseModel):
    """
    Schéma pour une liste de statistiques globales avec métadonnées.
    """
    model_config = ConfigDict(from_attributes=True)

    statistiques: StatistiquesGlobales = Field(
        ...,
        description="Liste des statistiques globales par entité"
    )