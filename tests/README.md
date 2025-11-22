# Tests du Backend Elections

## Structure des Tests

```
tests/
├── conftest.py           # Configuration globale des tests
├── unit/                 # Tests unitaires
│   ├── models/          # Tests des modèles SQLAlchemy
│   ├── services/        # Tests des services métier
│   └── schemas/         # Tests des schémas Pydantic
├── integration/         # Tests d'intégration
│   └── test_*_api.py   # Tests des endpoints API
└── fixtures/            # Données de test réutilisables
```

## Exécution des Tests

### Méthode 1: Script automatisé
```bash
python run_tests.py
```

### Méthode 2: Commandes pytest directes

**Tous les tests:**
```bash
pytest tests/ -v
```

**Tests unitaires uniquement:**
```bash
pytest tests/unit/ -v
```

**Tests d'intégration uniquement:**
```bash
pytest tests/integration/ -v
```

**Avec couverture de code:**
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

**Test spécifique:**
```bash
pytest tests/unit/models/test_region_model.py::TestRegionModel::test_create_region -v
```

## Configuration

### pytest.ini
- Configuration principale de pytest
- Marqueurs pour catégoriser les tests
- Options de couverture de code
- Filtres d'avertissements

### .coveragerc
- Configuration de la couverture de code
- Exclusions de fichiers
- Format des rapports

### conftest.py
- Fixtures partagées pour tous les tests
- Configuration de la base de données de test (SQLite)
- Client de test FastAPI

## Types de Tests

### Tests Unitaires
- **Models**: Validation des contraintes, relations, CRUD de base
- **Services**: Logique métier, validation des données, gestion d'erreurs
- **Schemas**: Sérialisation/désérialisation Pydantic

### Tests d'Intégration
- **API Endpoints**: Requêtes HTTP complètes
- **Base de données**: Intégration SQLAlchemy + PostgreSQL simulation
- **Workflows**: Scénarios utilisateur complets

## Bonnes Pratiques

### Isolation des Tests
- Chaque test utilise une transaction rollback
- Base de données SQLite en mémoire pour la rapidité
- Fixtures séparées pour éviter les interférences

### Nommage
- `test_*` pour les fonctions de test
- `Test*` pour les classes de test
- Noms descriptifs expliquant le scénario testé

### Structure d'un Test
```python
def test_nom_du_scenario(self, fixtures_necessaires):
    # Arrange: Préparer les données
    data = {"field": "value"}

    # Act: Exécuter l'action
    result = function_to_test(data)

    # Assert: Vérifier le résultat
    assert result.field == "expected_value"
```

## Métriques

### Couverture de Code
- Objectif: > 80% de couverture
- Rapport HTML généré dans `htmlcov/`
- Rapport terminal avec lignes manquantes

### Types d'Assertions
- Valeurs de retour
- Exceptions levées
- État de la base de données
- Codes de statut HTTP

## Dépendances de Test

```
pytest==8.3.4          # Framework de test
pytest-asyncio==0.24.0 # Support async/await
pytest-cov==6.0.0      # Couverture de code
httpx==0.28.1          # Client HTTP pour FastAPI
psycopg2-binary==2.9.10 # Driver PostgreSQL
```

## Debugging

### Tests en Mode Verbose
```bash
pytest tests/ -v -s
```

### Arrêt au Premier Échec
```bash
pytest tests/ -x
```

### Mode Debug avec PDB
```bash
pytest tests/ --pdb
```

### Logs Détaillés
```bash
pytest tests/ --log-cli-level=DEBUG
```