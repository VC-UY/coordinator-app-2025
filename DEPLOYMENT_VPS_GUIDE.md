# Guide de Déploiement du Coordinateur sur VPS

Ce guide vous accompagne dans le déploiement complet du coordinateur sur un serveur VPS Linux.

## Table des Matières
1. [Prérequis](#prérequis)
2. [Préparation du Serveur](#préparation-du-serveur)
3. [Installation de l'Application](#installation-de-lapplication)
4. [Configuration Redis](#configuration-redis)
5. [Configuration Nginx](#configuration-nginx)
6. [SSL/TLS avec Let's Encrypt](#ssltls-avec-lets-encrypt)
7. [Services Systemd](#services-systemd)
8. [Sécurité et Firewall](#sécurité-et-firewall)
9. [Monitoring et Logs](#monitoring-et-logs)
10. [Maintenance](#maintenance)

---

## Prérequis

### Serveur Minimum
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: 2 GB minimum (4 GB recommandé)
- **CPU**: 2 cores minimum
- **Disque**: 20 GB minimum
- **Réseau**: IP publique fixe

### Nom de Domaine
- Un nom de domaine pointant vers l'IP du serveur
- Exemple: `coordinator.example.com`

### Ports Nécessaires
- **80**: HTTP (redirection vers HTTPS)
- **443**: HTTPS (Nginx)
- **6380**: Redis Proxy (pour les connexions externes)
- **8410**: File Proxy (pour le transfert de fichiers)

---

## Préparation du Serveur

### 1. Connexion SSH
```bash
ssh root@votre-ip-serveur
```

### 2. Mise à Jour du Système
```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 3. Installation des Dépendances
```bash
# Ubuntu/Debian
apt install -y python3 python3-pip python3-venv \
    nginx redis-server git curl \
    ufw fail2ban certbot python3-certbot-nginx

# CentOS/RHEL
yum install -y python3 python3-pip python3-devel \
    nginx redis git curl \
    firewalld certbot python3-certbot-nginx
```

### 4. Créer un Utilisateur Système
```bash
# Créer l'utilisateur 'coordinator' sans shell interactif
useradd -r -s /bin/false -d /opt/coordinator coordinator
```

---

## Installation de l'Application

### 1. Créer le Répertoire d'Installation
```bash
mkdir -p /opt/coordinator
cd /opt/coordinator
```

### 2. Cloner ou Copier l'Application
```bash
# Option A: Via Git
git clone https://github.com/votre-repo/coordinator-app.git .

# Option B: Via SCP depuis votre machine locale
# Sur votre machine locale:
scp -r ./Coordinator-App/* root@votre-ip:/opt/coordinator/
```

### 3. Créer l'Environnement Virtuel
```bash
cd /opt/coordinator/coordinator_project
python3 -m venv exp-env
source exp-env/bin/activate
```

### 4. Installer les Dépendances Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Serveur WSGI pour production
```

### 5. Configuration Django

#### Modifier `settings.py`
```python
# /opt/coordinator/coordinator_project/coordinator_project/settings.py

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'VOTRE-CLE-SECRETE-UNIQUE'  # Générer avec: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['coordinator.example.com', 'votre-ip-publique']

# Database (utiliser PostgreSQL en production si nécessaire)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = '/opt/coordinator/static/'
STATIC_URL = '/static/'
```

### 6. Migrations et Static Files
```bash
source /opt/coordinator/coordinator_project/exp-env/bin/activate
cd /opt/coordinator/coordinator_project

# Appliquer les migrations
python manage.py migrate

# Créer un superuser (pour l'admin)
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### 7. Permissions
```bash
chown -R coordinator:coordinator /opt/coordinator
chmod -R 755 /opt/coordinator
```

---

## Configuration Redis

### 1. Configuration Redis Principal (Port 6379)
```bash
# Éditer /etc/redis/redis.conf
nano /etc/redis/redis.conf
```

Modifier les lignes suivantes:
```conf
# Bind sur localhost uniquement (sécurité)
bind 127.0.0.1

# Activer la persistance
save 900 1
save 300 10
save 60 10000

# Mot de passe Redis (recommandé)
requirepass VOTRE_MOT_DE_PASSE_REDIS_FORT
```

Redémarrer Redis:
```bash
systemctl restart redis-server
systemctl enable redis-server
```

### 2. Configurer le Proxy Redis (Port 6380)

Créer le fichier de configuration:
```bash
nano /opt/coordinator/redis_proxy_config.py
```

```python
# Configuration du proxy Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_PASSWORD = 'VOTRE_MOT_DE_PASSE_REDIS_FORT'

PROXY_HOST = '0.0.0.0'  # Écoute sur toutes les interfaces
PROXY_PORT = 6380

# Whiteliste des channels autorisés (sécurité)
ALLOWED_CHANNELS = [
    'coordinator/broadcast',
    'coordinator/task',
    'volunteer/*',
    'manager/*',
    'auth/*'
]
```

---

## Configuration Nginx

### 1. Créer la Configuration Nginx
```bash
nano /etc/nginx/sites-available/coordinator
```

```nginx
# Upstream pour Gunicorn (Django)
upstream coordinator_django {
    server 127.0.0.1:8000;
}

# Upstream pour le File Proxy
upstream file_proxy {
    server 127.0.0.1:8410;
}

# Redirection HTTP -> HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name coordinator.example.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name coordinator.example.com;

    # Certificats SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/coordinator.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/coordinator.example.com/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS (optionnel mais recommandé)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logs
    access_log /var/log/nginx/coordinator_access.log;
    error_log /var/log/nginx/coordinator_error.log;

    # Static files
    location /static/ {
        alias /opt/coordinator/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://coordinator_django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket pour Django Channels (si utilisé)
    location /ws/ {
        proxy_pass http://coordinator_django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # File Proxy (transfert de fichiers)
    location /files/ {
        proxy_pass http://file_proxy/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Timeouts augmentés pour les gros fichiers
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Limite de taille des uploads
        client_max_body_size 500M;
    }
}
```

### 2. Activer la Configuration
```bash
# Créer le lien symbolique
ln -s /etc/nginx/sites-available/coordinator /etc/nginx/sites-enabled/

# Supprimer la config par défaut
rm /etc/nginx/sites-enabled/default

# Tester la configuration
nginx -t

# Redémarrer Nginx
systemctl restart nginx
systemctl enable nginx
```

---

## SSL/TLS avec Let's Encrypt

### 1. Obtenir un Certificat SSL
```bash
# Arrêter Nginx temporairement
systemctl stop nginx

# Obtenir le certificat
certbot certonly --standalone -d coordinator.example.com

# Redémarrer Nginx
systemctl start nginx
```

### 2. Renouvellement Automatique
```bash
# Le renouvellement est automatique via cron/systemd timer
# Vérifier le timer
systemctl status certbot.timer

# Test manuel du renouvellement
certbot renew --dry-run
```

---

## Services Systemd

### 1. Service Django (Gunicorn)

Créer `/etc/systemd/system/coordinator-django.service`:
```ini
[Unit]
Description=Coordinator Django Application (Gunicorn)
After=network.target redis-server.service

[Service]
Type=notify
User=coordinator
Group=coordinator
WorkingDirectory=/opt/coordinator/coordinator_project
Environment="PATH=/opt/coordinator/coordinator_project/exp-env/bin"

ExecStart=/opt/coordinator/coordinator_project/exp-env/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/coordinator/gunicorn_access.log \
    --error-logfile /var/log/coordinator/gunicorn_error.log \
    coordinator_project.wsgi:application

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 2. Service Redis Proxy

Créer `/etc/systemd/system/coordinator-proxy.service`:
```ini
[Unit]
Description=Coordinator Redis Proxy
After=network.target redis-server.service

[Service]
Type=simple
User=coordinator
Group=coordinator
WorkingDirectory=/opt/coordinator
Environment="PATH=/opt/coordinator/coordinator_project/exp-env/bin"

ExecStart=/opt/coordinator/coordinator_project/exp-env/bin/python \
    /opt/coordinator/coordinator_project/redis_communication/proxy.py

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 3. Service File Proxy

Créer `/etc/systemd/system/coordinator-fileproxy.service`:
```ini
[Unit]
Description=Coordinator File Proxy Server
After=network.target

[Service]
Type=simple
User=coordinator
Group=coordinator
WorkingDirectory=/opt/coordinator
Environment="PATH=/opt/coordinator/coordinator_project/exp-env/bin"

ExecStart=/opt/coordinator/coordinator_project/exp-env/bin/python \
    /opt/coordinator/file_proxy.py \
    --host 0.0.0.0 \
    --port 8410 \
    --storage /opt/coordinator/file_storage

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 4. Activer et Démarrer les Services
```bash
# Créer les répertoires de logs
mkdir -p /var/log/coordinator
chown coordinator:coordinator /var/log/coordinator

# Recharger systemd
systemctl daemon-reload

# Activer les services au démarrage
systemctl enable coordinator-django
systemctl enable coordinator-proxy
systemctl enable coordinator-fileproxy

# Démarrer les services
systemctl start coordinator-django
systemctl start coordinator-proxy
systemctl start coordinator-fileproxy

# Vérifier le statut
systemctl status coordinator-django
systemctl status coordinator-proxy
systemctl status coordinator-fileproxy
```

---

## Sécurité et Firewall

### 1. Configuration UFW (Ubuntu/Debian)
```bash
# Activer UFW
ufw enable

# SSH (IMPORTANT: à faire en premier!)
ufw allow 22/tcp

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Redis Proxy (uniquement pour IPs autorisées)
# Option 1: Ouvert à tous (à éviter en production)
ufw allow 6380/tcp

# Option 2: Restreindre par IP (recommandé)
ufw allow from IP_DU_MANAGER to any port 6380 proto tcp
ufw allow from IP_DU_VOLUNTEER to any port 6380 proto tcp

# File Proxy
ufw allow 8410/tcp

# Vérifier les règles
ufw status verbose
```

### 2. Configuration Firewalld (CentOS/RHEL)
```bash
# Activer firewalld
systemctl enable firewalld
systemctl start firewalld

# HTTP/HTTPS
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# Redis Proxy
firewall-cmd --permanent --add-port=6380/tcp

# File Proxy
firewall-cmd --permanent --add-port=8410/tcp

# Recharger
firewall-cmd --reload
```

### 3. Fail2Ban (Protection contre les attaques)
```bash
# Configuration pour Nginx
nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/coordinator_error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/coordinator_error.log
maxretry = 10
```

```bash
systemctl restart fail2ban
systemctl enable fail2ban
```

---

## Monitoring et Logs

### 1. Vérifier les Logs des Services
```bash
# Django (Gunicorn)
journalctl -u coordinator-django -f

# Redis Proxy
journalctl -u coordinator-proxy -f

# File Proxy
journalctl -u coordinator-fileproxy -f

# Nginx
tail -f /var/log/nginx/coordinator_access.log
tail -f /var/log/nginx/coordinator_error.log
```

### 2. Rotation des Logs
```bash
# Créer /etc/logrotate.d/coordinator
nano /etc/logrotate.d/coordinator
```

```conf
/var/log/coordinator/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 coordinator coordinator
    sharedscripts
    postrotate
        systemctl reload coordinator-django > /dev/null 2>&1 || true
    endscript
}
```

### 3. Monitoring avec htop
```bash
apt install htop
htop
```

---

## Maintenance

### 1. Mise à Jour de l'Application
```bash
# Arrêter les services
systemctl stop coordinator-django coordinator-proxy coordinator-fileproxy

# Mise à jour du code
cd /opt/coordinator
git pull  # ou copier les nouveaux fichiers

# Activer l'environnement virtuel
source coordinator_project/exp-env/bin/activate

# Mettre à jour les dépendances
pip install -r coordinator_project/requirements.txt

# Migrations Django
cd coordinator_project
python manage.py migrate
python manage.py collectstatic --noinput

# Redémarrer les services
systemctl start coordinator-django coordinator-proxy coordinator-fileproxy
```

### 2. Backup de la Base de Données
```bash
# Script de backup automatique
nano /opt/coordinator/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/coordinator/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup SQLite
cp /opt/coordinator/coordinator_project/db.sqlite3 \
   $BACKUP_DIR/db_$DATE.sqlite3

# Compresser
gzip $BACKUP_DIR/db_$DATE.sqlite3

# Garder seulement les 30 derniers jours
find $BACKUP_DIR -name "db_*.sqlite3.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x /opt/coordinator/backup.sh

# Ajouter au crontab (tous les jours à 2h du matin)
crontab -e
```

```cron
0 2 * * * /opt/coordinator/backup.sh >> /var/log/coordinator/backup.log 2>&1
```

### 3. Surveiller l'Espace Disque
```bash
# Vérifier l'espace disque
df -h

# Nettoyer les logs anciens si nécessaire
journalctl --vacuum-time=30d
```

---

## Checklist de Déploiement

- [ ] Serveur VPS configuré avec IP publique
- [ ] Nom de domaine configuré (DNS A record)
- [ ] Dépendances système installées
- [ ] Application installée dans `/opt/coordinator`
- [ ] `settings.py` configuré pour production (DEBUG=False, SECRET_KEY, ALLOWED_HOSTS)
- [ ] Migrations Django appliquées
- [ ] Static files collectés
- [ ] Redis installé et sécurisé (mot de passe)
- [ ] Nginx configuré avec proxy vers Django et File Proxy
- [ ] Certificat SSL obtenu avec Let's Encrypt
- [ ] Services systemd créés et activés
- [ ] Firewall configuré (ports 80, 443, 6380, 8410)
- [ ] Fail2Ban activé
- [ ] Rotation des logs configurée
- [ ] Script de backup configuré
- [ ] Test de connexion depuis Manager et Volunteer

---

## Support et Dépannage

### Problème: Django ne démarre pas
```bash
# Vérifier les logs
journalctl -u coordinator-django -n 50

# Tester manuellement
cd /opt/coordinator/coordinator_project
source exp-env/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Problème: Nginx retourne 502 Bad Gateway
```bash
# Vérifier que Gunicorn écoute sur le bon port
netstat -tulpn | grep 8000

# Vérifier les permissions
ls -la /opt/coordinator/coordinator_project/db.sqlite3
```

### Problème: Redis Proxy ne se connecte pas
```bash
# Vérifier que Redis écoute
redis-cli -a VOTRE_MOT_DE_PASSE ping

# Vérifier les logs du proxy
journalctl -u coordinator-proxy -f
```

### Problème: Certificat SSL expiré
```bash
# Renouveler manuellement
certbot renew

# Recharger Nginx
systemctl reload nginx
```

---

**Félicitations!** 🎉 Votre coordinateur est maintenant déployé en production sur un VPS sécurisé.
