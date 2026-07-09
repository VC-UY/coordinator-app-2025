# Déploiement depuis ce dépôt unique

Ce dossier permet de lancer le coordinateur **directement depuis `coordinator-app-2025`**.

## Contenu

- `docker-compose.coordinator.yml`: stack autonome coordinator
- `docker/`: Dockerfiles coordinator API / proxy / frontend
- `nginx/`: config Nginx frontend
- `env.production.example`: modèle d'environnement production

## Démarrage local rapide

```bash
cd deploy
cp env.production.example .env.production
docker compose -f docker-compose.coordinator.yml --env-file .env.production up -d --build
```

Services exposés:

- Coordinator API: `http://localhost:8001`
- Coordinator Frontend: `http://localhost:5173`
- Redis volontaire stable: `localhost:6380`
- Redis interne: `localhost:6379` (dans le réseau compose)
- MongoDB: `localhost:27017` (interne réseau compose)

## Vérifications

```bash
redis-cli -h 127.0.0.1 -p 6380 ping
curl -i http://127.0.0.1:8001/api/
docker compose -f docker-compose.coordinator.yml ps
```

## Arrêt

```bash
docker compose -f docker-compose.coordinator.yml down
```
