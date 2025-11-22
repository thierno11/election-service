"""Schémas Pydantic pour les participations."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipationSchema(BaseModel):
    """
    Schéma pour la création et modification d'une participation.

    Attributes:
        type_election: Type de l'élection
        id_bureau: Identifiant du bureau de vote
        nombre_electeur: Nombre d'électeurs inscrits
        nombre_votant: Nombre de votants
        nombre_votant_hors_bureau: Nombre de votants hors bureau
        nombre_bulletin_null: Nombre de bulletins nuls
        nombre_suffrage: Nombre de suffrages exprimés
        date_election: Date de l'élection
    """
    model_config = ConfigDict(from_attributes=True)

    type_election: str = Field(
        ...,
        description="Type de l'élection",
        examples=["PRESIDENTIELLE"]
    )
    commune: str
    centre: str
    bureau: int = Field(
        ...,
        description="Identifiant du bureau de vote",
        examples=[1]
    )

    nombre_electeur: int = Field(
        default=0,
        ge=0,
        description="Nombre d'électeurs inscrits"
    )

    nombre_votant: int = Field(
        default=0,
        ge=0,
        description="Nombre de votants"
    )

    nombre_votant_hors_bureau: int = Field(
        default=0,
        ge=0,
        description="Nombre de votants hors bureau"
    )

    nombre_bulletin_null: int = Field(
        default=0,
        ge=0,
        description="Nombre de bulletins nuls"
    )

    nombre_suffrage: int = Field(
        default=0,
        ge=0,
        description="Nombre de suffrages exprimés"
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection",
        examples=["2024-12-31"]
    )



class ParticipationReponse(BaseModel):
    """
    Schéma de réponse pour une participation.

    Attributes:
        id_election: Identifiant de l'élection
        id_bureau: Identifiant du bureau de vote
        nombre_electeur: Nombre d'électeurs inscrits
        nombre_votant: Nombre de votants
        nombre_votant_hors_bureau: Nombre de votants hors bureau
        nombre_bulletin_null: Nombre de bulletins nuls
        nombre_suffrage: Nombre de suffrages exprimés
        date_election: Date de l'élection
        created_at: Date de création
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

    nombre_electeur: int = Field(
        ...,
        description="Nombre d'électeurs inscrits"
    )

    nombre_votant: int = Field(
        ...,
        description="Nombre de votants"
    )

    nombre_votant_hors_bureau: int = Field(
        ...,
        description="Nombre de votants hors bureau"
    )

    nombre_bulletin_null: int = Field(
        ...,
        description="Nombre de bulletins nuls"
    )

    nombre_suffrage: int = Field(
        ...,
        description="Nombre de suffrages exprimés"
    )

    date_election: date = Field(
        ...,
        description="Date de l'élection"
    )

    created_at: datetime = Field(
        ...,
        description="Date de création de l'enregistrement"
    )


class StatistiquesParticipation(BaseModel):
    """
    Schéma pour les statistiques de participation agrégées.

    Attributes:
        niveau: Niveau géographique (bureau, centre, commune, departement, region, national)
        identifiant: Identifiant de l'entité (optionnel pour niveau national)
        nom: Nom de l'entité
        total_electeurs: Nombre total d'électeurs inscrits
        total_votants: Nombre total de votants
        total_votants_hors_bureau: Nombre total de votants hors bureau
        total_bulletins_nuls: Nombre total de bulletins nuls
        total_suffrages: Nombre total de suffrages exprimés
        taux_participation: Taux de participation en pourcentage
        taux_suffrages_valides: Taux de suffrages valides par rapport aux votants
        nombre_bureaux: Nombre de bureaux de vote concernés
    """
    model_config = ConfigDict(from_attributes=True)


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

    total_votants_hors_bureau: int = Field(
        ...,
        ge=0,
        description="Nombre total de votants hors bureau"
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

    taux_suffrages_valides: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de suffrages valides par rapport aux votants"
    )


class StatistiquesParticipationListe(BaseModel):
    """
    Schéma pour une liste de statistiques avec métadonnées.

    Attributes:
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        niveau: Niveau géographique des statistiques
        total_elements: Nombre total d'éléments dans la liste
        statistiques: Liste des statistiques
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

    niveau: str = Field(
        ...,
        description="Niveau géographique des statistiques"
    )

    total_elements: int = Field(
        ...,
        ge=0,
        description="Nombre total d'éléments dans la liste"
    )

    statistiques: list[StatistiquesParticipation] = Field(
        ...,
        description="Liste des statistiques de participation"
    )


class RepartitionParticipationGeographique(BaseModel):
    """
    Schéma pour la répartition géographique de la participation.

    Attributes:
        identifiant: Identifiant de l'entité géographique
        nom: Nom de l'entité géographique
        total_electeurs: Nombre d'électeurs inscrits
        total_votants: Nombre de votants
        total_votants_hors_bureau: Nombre de votants hors bureau
        total_bulletins_nuls: Nombre de bulletins nuls
        total_suffrages: Nombre de suffrages exprimés
        taux_participation: Taux de participation pour cette entité
        taux_suffrages_valides: Taux de suffrages valides pour cette entité
    """
    model_config = ConfigDict(from_attributes=True)

    identifiant: int = Field(
        ...,
        description="Identifiant de l'entité géographique"
    )

    nom: str = Field(
        ...,
        description="Nom de l'entité géographique"
    )

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

    total_votants_hors_bureau: int = Field(
        ...,
        ge=0,
        description="Nombre de votants hors bureau"
    )

    total_bulletins_nuls: int = Field(
        ...,
        ge=0,
        description="Nombre de bulletins nuls"
    )

    total_suffrages: int = Field(
        ...,
        ge=0,
        description="Nombre de suffrages exprimés"
    )

    taux_participation: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de participation pour cette entité"
    )

    taux_suffrages_valides: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de suffrages valides pour cette entité"
    )


class StatistiquesParticipationGlobales(BaseModel):
    """
    Schéma pour les statistiques globales de participation avec répartition géographique.

    Attributes:
        id_election: Identifiant de l'élection
        date_election: Date de l'élection
        niveau: Niveau géographique
        identifiant: Identifiant de l'entité
        nom: Nom de l'entité
        total_electeurs: Nombre total d'électeurs inscrits
        total_votants: Nombre total de votants
        total_votants_hors_bureau: Nombre total de votants hors bureau
        total_bulletins_nuls: Nombre total de bulletins nuls
        total_suffrages: Nombre total de suffrages exprimés
        taux_participation: Taux de participation en pourcentage
        taux_suffrages_valides: Taux de suffrages valides
        nombre_bureaux: Nombre de bureaux concernés
        repartition_geographique: Répartition géographique de la participation
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

    niveau: str = Field(
        ...,
        description="Niveau géographique",
        examples=["bureau", "centre", "commune", "departement", "region", "national"]
    )

    identifiant: Optional[int] = Field(
        None,
        description="Identifiant de l'entité (null pour niveau national)"
    )

    nom: str = Field(
        ...,
        description="Nom de l'entité"
    )

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

    total_votants_hors_bureau: int = Field(
        ...,
        ge=0,
        description="Nombre total de votants hors bureau"
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

    taux_suffrages_valides: float = Field(
        ...,
        ge=0,
        le=100,
        description="Taux de suffrages valides par rapport aux votants"
    )

    nombre_bureaux: int = Field(
        ...,
        ge=0,
        description="Nombre de bureaux concernés"
    )

    repartition_geographique: list[RepartitionParticipationGeographique] = Field(
        ...,
        description="Répartition géographique de la participation (par région si national, par département si région)"
    )


class StatistiquesParticipationGlobalesListe(BaseModel):
    """
    Schéma pour une liste de statistiques globales de participation avec métadonnées.
    """
    model_config = ConfigDict(from_attributes=True)

    statistiques: StatistiquesParticipationGlobales = Field(
        ...,
        description="Statistiques globales de participation"
    )


class EvolutionParticipationTemporelle(BaseModel):
    """
    Schéma pour l'évolution temporelle des participations par intervalle de 15 minutes.

    Attributes:
        heure_debut: Début de l'intervalle de 15 minutes
        heure_fin: Fin de l'intervalle de 15 minutes
        nombre_participations: Nombre de participations créées dans cet intervalle
        cumul_participations: Nombre cumulé de participations jusqu'à cet intervalle
        pourcentage_cumul: Pourcentage cumulé par rapport au total
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

    nombre_participations: int = Field(
        ...,
        ge=0,
        description="Nombre de participations créées dans cet intervalle"
    )

    cumul_participations: int = Field(
        ...,
        ge=0,
        description="Nombre cumulé de participations jusqu'à cet intervalle"
    )

    pourcentage_cumul: float = Field(
        ...,
        ge=0,
        le=100,
        description="Pourcentage cumulé par rapport au total"
    )


class EvolutionParticipationTemporelleListe(BaseModel):
    """
    Schéma pour une liste d'évolutions temporelles des participations.
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

    total_participations: int = Field(
        ...,
        ge=0,
        description="Nombre total de participations"
    )

    duree_totale_minutes: int = Field(
        ...,
        ge=0,
        description="Durée totale en minutes entre la première et dernière participation"
    )

    nombre_intervalles: int = Field(
        ...,
        ge=0,
        description="Nombre d'intervalles de 15 minutes"
    )

    evolution: list[EvolutionParticipationTemporelle] = Field(
        ...,
        description="Liste des évolutions par intervalle de 15 minutes"
    )