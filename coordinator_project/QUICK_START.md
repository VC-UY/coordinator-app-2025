# 🚀 Guide de Démarrage Rapide - Coordinator

## Démarrage Simple

### Une seule commande pour tout démarrer !

```bash
python manage.py runall
```

Cette commande démarre automatiquement :
- ✅ Le serveur Django (port 8080)
- ✅ Le proxy Redis (port 6380)
- ✅ Le proxy de fichiers (port 8000)

## Options de Configuration

```bash
python manage.py runall [OPTIONS]
```

### Options disponibles :

| Option | Défaut | Description |
|--------|--------|-------------|
| `--django-port` | 8080 | Port du serveur Django |
| `--redis-host` | 0.0.0.0 | Hôte Redis |
| `--redis-port` | 6379 | Port Redis |
| `--proxy-port` | 6380 | Port du proxy Redis |
| `--logs-dir` | logs | Répertoire des logs |

### Exemples :

```bash
# Utiliser un port Django différent
python manage.py runall --django-port 8000

# Spécifier un répertoire de logs personnalisé
python manage.py runall --logs-dir /var/log/coordinator

# Configuration complète
python manage.py runall \
  --django-port 8080 \
  --redis-host localhost \
  --redis-port 6379 \
  --proxy-port 6380 \
  --logs-dir logs
```

## 📊 Logs Séparés

Les logs sont automatiquement séparés dans des fichiers différents :

```
logs/
├── django_20251114_120000.log     # Logs Django avec timestamp
├── proxy_20251114_120000.log      # Logs Proxy avec timestamp
├── django_latest.log -> django_20251114_120000.log  # Lien symbolique vers le dernier
└── proxy_latest.log  -> proxy_20251114_120000.log   # Lien symbolique vers le dernier
```

### Visualiser les logs en temps réel :

```bash
# Logs Django (derniers)
tail -f logs/django_latest.log

# Logs Proxy (derniers)
tail -f logs/proxy_latest.log

# Les deux en parallèle
tail -f logs/django_latest.log logs/proxy_latest.log
```

### Avec tmux (recommandé) :

```bash
# Créer une session avec 2 panneaux
tmux new-session \; \
  split-window -h \; \
  send-keys 'tail -f logs/django_latest.log' C-m \; \
  select-pane -t 0 \; \
  send-keys 'tail -f logs/proxy_latest.log' C-m
```

## 🛑 Arrêt des Services

Pour arrêter tous les services :

```
Ctrl+C
```

Les deux services (Django et Proxy) seront arrêtés proprement.

## 📋 Vérification des Services

### Vérifier que tout fonctionne :

```bash
# Serveur Django
curl http://localhost:8080/

# Proxy Redis (avec redis-cli)
redis-cli -h localhost -p 6380 PING

# Proxy de fichiers
curl http://localhost:8000/health
```

### Vérifier les processus :

```bash
# Voir les processus Python
ps aux | grep manage.py

# Vérifier les ports ouverts
netstat -tulpn | grep -E '8080|6380|8000'
```

## 🔧 Démarrage Séparé (Mode Avancé)

Si vous préférez démarrer les services séparément :

```bash
# Démarrer seulement le proxy Redis
python manage.py start_redis_proxy

# Démarrer seulement Django
python manage.py runserver 8080
```

## 📝 Structure des Logs

Chaque fichier de log contient :

### Django (`django_*.log`) :
- Requêtes HTTP
- Erreurs Django
- Messages de l'application
- Queries SQL (si DEBUG=True)

### Proxy (`proxy_*.log`) :
- Messages Redis pub/sub
- Connexions clients
- Routage de fichiers
- Erreurs du proxy

## 🚨 Dépannage

### Le serveur ne démarre pas :

```bash
# Vérifier si les ports sont déjà utilisés
lsof -i :8080  # Django
lsof -i :6380  # Proxy Redis
lsof -i :8000  # Proxy de fichiers

# Tuer les processus si nécessaire
kill -9 <PID>
```

### Vérifier les logs d'erreur :

```bash
# Dernières erreurs Django
tail -n 50 logs/django_latest.log | grep ERROR

# Dernières erreurs Proxy
tail -n 50 logs/proxy_latest.log | grep ERROR
```

### Nettoyer les anciens logs :

```bash
# Supprimer les logs de plus de 7 jours
find logs/ -name "*.log" -type f -mtime +7 -delete

# Garder seulement les 10 derniers logs
ls -t logs/*.log | tail -n +11 | xargs rm -f
```

## 🎯 Utilisation en Production

### Avec systemd :

Créer `/etc/systemd/system/coordinator.service` :

```ini
[Unit]
Description=Coordinator Service
After=network.target redis.target

[Service]
Type=simple
User=coordinator
WorkingDirectory=/path/to/coordinator_project
Environment="DJANGO_SETTINGS_MODULE=coordinator_project.settings"
ExecStart=/usr/bin/python3 manage.py runall
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable coordinator
sudo systemctl start coordinator
sudo systemctl status coordinator
```

### Avec Docker :

```dockerfile
FROM python:3.8

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080 6380 8000

CMD ["python", "manage.py", "runall"]
```

## 📚 Commandes Utiles

```bash
# Démarrer tous les services
python manage.py runall

# Voir l'aide
python manage.py runall --help

# Vérifier les migrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic
```

## ✅ Checklist de Démarrage

- [ ] Redis est installé et fonctionne
- [ ] Les dépendances Python sont installées (`pip install -r requirements.txt`)
- [ ] Les migrations sont appliquées (`python manage.py migrate`)
- [ ] Les ports 8080, 6380, 8000 sont disponibles
- [ ] Le répertoire `logs/` est accessible en écriture
- [ ] Lancer `python manage.py runall`
- [ ] Vérifier les logs pour confirmer que tout démarre correctement

---

**Besoin d'aide ?** Consultez les logs ou ouvrez une issue sur GitHub.
