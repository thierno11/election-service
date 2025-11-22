# Configuration ELK Stack pour l'API Électorale

## Architecture

Le stack ELK est composé de :
- **Elasticsearch** : Stockage et indexation des logs
- **Logstash** : Collecte et traitement des logs
- **Kibana** : Visualisation et analyse des logs

## Démarrage

### 1. Lancer le stack ELK

```bash
docker-compose up -d
```

### 2. Vérifier que les services sont actifs

```bash
docker-compose ps
```

### 3. Accéder aux services

- **Kibana** : http://localhost:5601
- **Elasticsearch** : http://localhost:9200
- **API** : http://localhost:8000

## Configuration des logs

Les logs sont automatiquement envoyés à Elasticsearch au format JSON avec les informations suivantes :
- `timestamp` : Date et heure du log
- `level` : Niveau de log (INFO, WARNING, ERROR, etc.)
- `logger` : Nom du logger
- `message` : Message du log
- `module` : Module source
- `function` : Fonction source
- `line` : Numéro de ligne

## Utilisation de Kibana

### 1. Créer un Index Pattern

1. Aller sur http://localhost:5601
2. Menu → Stack Management → Index Patterns
3. Cliquer sur "Create index pattern"
4. Entrer `elections-logs-*` comme pattern
5. Sélectionner `@timestamp` comme Time field
6. Cliquer sur "Create index pattern"

### 2. Visualiser les logs

1. Menu → Discover
2. Sélectionner l'index pattern `elections-logs-*`
3. Vous verrez tous les logs de l'application

### 3. Créer des dashboards

1. Menu → Dashboard → Create dashboard
2. Ajouter des visualisations (graphiques, tableaux, etc.)
3. Exemples de visualisations utiles :
   - Nombre de logs par niveau (INFO, ERROR, etc.)
   - Logs par module
   - Tendances temporelles des erreurs

## Filtres utiles dans Kibana

```
# Logs d'erreur uniquement
log_level: "ERROR"

# Logs d'un module spécifique
module: "main"

# Logs contenant un texte
message: *database*
```

## Arrêter le stack

```bash
docker-compose down
```

## Nettoyer les données

```bash
docker-compose down -v
```