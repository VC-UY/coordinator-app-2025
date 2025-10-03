#!/bin/bash
# Installation et configuration automatique pour les tests du proxy Redis

set -e

echo "🔧 INSTALLATION ET CONFIGURATION DU PROXY REDIS"
echo "================================================="

# Vérifier les privilèges
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Ce script ne doit PAS être exécuté en tant que root"
    echo "   Exécutez-le avec votre utilisateur normal"
    exit 1
fi

# Détecter la distribution
if command -v apt &> /dev/null; then
    DISTRO="ubuntu"
elif command -v yum &> /dev/null; then
    DISTRO="centos"
elif command -v pacman &> /dev/null; then
    DISTRO="arch"
else
    echo "❌ Distribution non supportée"
    exit 1
fi

echo "📦 Installation des dépendances..."

# Installation Redis
if ! command -v redis-server &> /dev/null; then
    echo "📥 Installation de Redis..."
    case $DISTRO in
        ubuntu)
            sudo apt update
            sudo apt install -y redis-server redis-tools
            ;;
        centos)
            sudo yum install -y epel-release
            sudo yum install -y redis
            ;;
        arch)
            sudo pacman -S redis
            ;;
    esac
else
    echo "✅ Redis déjà installé"
fi

# Installation Python et pip
if ! command -v python3 &> /dev/null; then
    echo "📥 Installation de Python3..."
    case $DISTRO in
        ubuntu)
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        centos)
            sudo yum install -y python3 python3-pip
            ;;
        arch)
            sudo pacman -S python python-pip
            ;;
    esac
else
    echo "✅ Python3 déjà installé"
fi

# Installation des dépendances Python
echo "📥 Installation des dépendances Python..."
pip3 install --user asyncio aioredis redis psutil

# Configuration des limites système (temporaire)
echo "🔧 Configuration des limites système..."

# File descriptors pour la session courante
ulimit -n 65536 2>/dev/null || echo "⚠️  Impossible de définir ulimit (normal sans sudo)"

# Vérifier la configuration Redis
echo "🔍 Vérification de la configuration Redis..."

# Créer un fichier de configuration Redis optimisé
REDIS_CONF="/tmp/redis_proxy_test.conf"
cat > $REDIS_CONF << 'EOF'
# Configuration Redis optimisée pour tests de charge
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 60
tcp-backlog 8192
maxclients 100000

# Désactiver la persistance pour les tests
save ""
stop-writes-on-bgsave-error no

# Configuration mémoire
maxmemory-policy allkeys-lru

# Logging minimal
loglevel warning
logfile ""

# Autres optimisations
databases 1
EOF

echo "✅ Configuration Redis créée: $REDIS_CONF"

# Créer le répertoire de logs
mkdir -p logs

# Fonction pour démarrer Redis avec la config optimisée
cat > start_redis_test.sh << 'EOF'
#!/bin/bash
echo "🚀 Démarrage de Redis avec configuration optimisée..."

# Arrêter Redis existant
redis-cli shutdown 2>/dev/null || true
sleep 1

# Démarrer avec la config de test
redis-server /tmp/redis_proxy_test.conf --daemonize yes

# Vérifier le démarrage
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis démarré avec succès"
    redis-cli config get maxclients
else
    echo "❌ Échec du démarrage de Redis"
    exit 1
fi
EOF

chmod +x start_redis_test.sh

# Fonction pour arrêter Redis
cat > stop_redis_test.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt de Redis..."
redis-cli shutdown 2>/dev/null || true
echo "✅ Redis arrêté"
EOF

chmod +x stop_redis_test.sh

# Script de vérification des performances système
cat > check_system_limits.py << 'EOF'
#!/usr/bin/env python3
"""
Vérification des limites système pour les tests de charge.
"""

import os
import sys
import resource
import socket

def check_system_limits():
    print("🔍 VÉRIFICATION DES LIMITES SYSTÈME")
    print("=" * 40)
    
    # File descriptors
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    print(f"📁 File descriptors: {soft:,} (soft) / {hard:,} (hard)")
    
    if soft < 10000:
        print("⚠️  Limite de file descriptors faible")
        print("   Recommandé: au moins 65536")
    else:
        print("✅ Limites de file descriptors OK")
    
    # Processus
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
        print(f"🔄 Processus: {soft:,} (soft) / {hard:,} (hard)")
    except:
        print("🔄 Processus: Non disponible sur ce système")
    
    # Test de création de sockets
    print("\n🔌 Test de création de sockets...")
    max_sockets = 0
    sockets = []
    
    try:
        for i in range(1000):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockets.append(sock)
            max_sockets += 1
        print(f"✅ {max_sockets:,} sockets créées avec succès")
    except Exception as e:
        print(f"⚠️  Limite atteinte à {max_sockets:,} sockets: {e}")
    finally:
        for sock in sockets:
            sock.close()
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if soft < 65536:
        print("• Augmentez les file descriptors:")
        print("  ulimit -n 65536")
    
    print("• Pour des tests persistants, modifiez /etc/security/limits.conf")
    print("• Surveillez l'utilisation mémoire pendant les tests")

if __name__ == "__main__":
    check_system_limits()
EOF

chmod +x check_system_limits.py

# Documentation d'utilisation
cat > README_TESTS.md << 'EOF'
# Tests du Proxy Redis - Guide d'utilisation

## 🚀 Démarrage rapide

1. **Préparer l'environnement** (déjà fait par ce script)
   ```bash
   ./setup_proxy_tests.sh
   ```

2. **Vérifier les limites système**
   ```bash
   python3 check_system_limits.py
   ```

3. **Démarrer Redis optimisé**
   ```bash
   ./start_redis_test.sh
   ```

4. **Lancer les tests complets**
   ```bash
   python3 scripts/start_and_test_proxy.py
   ```

## 🧪 Tests disponibles

### Tests de validation
```bash
python3 tests/test_proxy_validation.py
```

### Tests de charge progressifs
```bash
python3 scripts/start_and_test_proxy.py
```

## 📊 Surveillance

- Logs du proxy: `logs/proxy.log`
- Métriques système: `htop` ou `ps aux | grep redis`
- Connexions réseau: `ss -tuln | grep 6380`

## 🛑 Arrêt

```bash
./stop_redis_test.sh
# Le proxy s'arrête automatiquement avec Ctrl+C
```

## 🔧 Dépannage

### Proxy ne démarre pas
- Vérifiez que Redis est démarré: `redis-cli ping`
- Vérifiez le port 6380: `ss -tuln | grep 6380`

### Erreurs de connexion
- Augmentez les file descriptors: `ulimit -n 65536`
- Vérifiez les limites: `python3 check_system_limits.py`

### Performance faible
- Surveillez la RAM: `free -h`
- Surveillez le CPU: `top`
- Vérifiez les erreurs: `dmesg | tail`
EOF

echo ""
echo "✅ INSTALLATION TERMINÉE !"
echo "=========================="
echo ""
echo "📋 Prochaines étapes:"
echo "1. Vérifiez les limites système:"
echo "   python3 check_system_limits.py"
echo ""
echo "2. Démarrez Redis optimisé:"
echo "   ./start_redis_test.sh"
echo ""
echo "3. Lancez les tests complets:"
echo "   python3 scripts/start_and_test_proxy.py"
echo ""
echo "📖 Consultez README_TESTS.md pour plus de détails"