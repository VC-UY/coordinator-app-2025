#!/bin/bash
# filepath: /home/sergeo/Master-II/Recherches/Projet_M_I/Groupe C Coordinator/v1/Coordinator-App/scripts/optimize_system.sh

echo "🔧 Optimisation système pour 100K+ connexions"

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Sauvegarder les configurations actuelles
backup_dir="/tmp/system_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "💾 Sauvegarde des configurations dans $backup_dir"
cp /etc/security/limits.conf "$backup_dir/"
cp /etc/sysctl.conf "$backup_dir/"

# Augmenter les limites de file descriptors
echo "📁 Configuration des limites de fichiers"
cat >> /etc/security/limits.conf << 'EOF'
# Optimisations pour proxy Redis haute performance
* soft nofile 1048576
* hard nofile 1048576
root soft nofile 1048576
root hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
EOF

# Paramètres kernel pour haute performance réseau
echo "🌐 Configuration des paramètres réseau"
cat >> /etc/sysctl.conf << 'EOF'

# === OPTIMISATIONS PROXY REDIS ===
# Network connection limits
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 30000

# TCP connection optimization
net.ipv4.tcp_max_tw_buckets = 400000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# File and memory limits
fs.file-max = 2097152
fs.nr_open = 2097152
vm.max_map_count = 262144

# TCP buffer sizes for high throughput
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 262144
net.core.wmem_default = 262144

# Memory management
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Security (prevent SYN flood)
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 3
net.ipv4.tcp_synack_retries = 3
EOF

# Appliquer les changements sysctl
echo "⚡ Application des paramètres kernel"
sysctl -p

# Configuration systemd pour les services
echo "🔧 Configuration systemd"
mkdir -p /etc/systemd/system/redis-proxy.service.d/
cat > /etc/systemd/system/redis-proxy.service.d/override.conf << 'EOF'
[Service]
LimitNOFILE=1048576
LimitNPROC=1048576
[EOF]

# Configuration ulimit pour la session courante
echo "📊 Configuration ulimit session"
ulimit -n 1048576
ulimit -u 1048576

# Vérification Redis
echo "🔍 Vérification configuration Redis"
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis trouvé"
    
    # Suggestions de configuration Redis
    cat > /tmp/redis_optimization.conf << 'EOF'
# Configuration Redis pour haute performance
maxclients 100000
tcp-keepalive 60
timeout 0
tcp-backlog 65535
maxmemory-policy allkeys-lru
save ""
stop-writes-on-bgsave-error no
EOF
    
    echo "📝 Configuration Redis suggérée créée dans /tmp/redis_optimization.conf"
    echo "   Ajoutez ces paramètres à votre redis.conf"
else
    echo "⚠️  Redis non trouvé, installez Redis si nécessaire"
fi

# Installation des dépendances Python si nécessaire
echo "🐍 Vérification dépendances Python"
if command -v pip3 &> /dev/null; then
    pip3 install asyncio aioredis psutil
    echo "✅ Dépendances Python installées"
else
    echo "⚠️  pip3 non trouvé, installez manuellement: asyncio aioredis psutil"
fi

# Script de monitoring des performances
cat > /usr/local/bin/proxy-monitor << 'EOF'
#!/bin/bash
# Monitoring en temps réel du proxy Redis

echo "🖥️  Monitoring Proxy Redis - $(date)"
echo "================================"

while true; do
    clear
    echo "🖥️  Monitoring Proxy Redis - $(date)"
    echo "================================"
    
    # Connexions réseau
    echo "📡 CONNEXIONS RÉSEAU:"
    ss -tuln | grep :6380 || echo "Port 6380 non utilisé"
    echo "Active: $(ss -t state established | grep :6380 | wc -l) connexions"
    
    # Utilisation mémoire
    echo ""
    echo "💾 MÉMOIRE:"
    free -h
    
    # Utilisation CPU
    echo ""
    echo "🖥️  CPU:"
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "Utilisation: " 100 - $1 "%"}'
    
    # File descriptors
    echo ""
    echo "📁 FILE DESCRIPTORS:"
    echo "Limit: $(ulimit -n)"
    echo "Utilisés: $(lsof | wc -l 2>/dev/null || echo "N/A")"
    
    # Processus Python
    echo ""
    echo "🐍 PROCESSUS PYTHON:"
    ps aux | grep python | grep -v grep | wc -l | awk '{print "Processus actifs: " $1}'
    
    echo ""
    echo "Appuyez sur Ctrl+C pour quitter"
    sleep 5
done
EOF

chmod +x /usr/local/bin/proxy-monitor

# Création du service systemd pour le proxy
cat > /etc/systemd/system/redis-proxy.service << 'EOF'
[Unit]
Description=Redis Proxy High Performance
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=proxy
Group=proxy
WorkingDirectory=/opt/redis-proxy
ExecStart=/usr/bin/python3 /opt/redis-proxy/proxy.py
Restart=always
RestartSec=5
LimitNOFILE=1048576
LimitNPROC=1048576

# Optimisations mémoire
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONOPTIMIZE=1

[Install]
WantedBy=multi-user.target
EOF

# Créer l'utilisateur proxy si nécessaire
if ! id "proxy" &>/dev/null; then
    echo "👤 Création utilisateur proxy"
    useradd -r -s /bin/false proxy
fi

echo ""
echo "✅ OPTIMISATION SYSTÈME TERMINÉE"
echo "================================="
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo "1. Redémarrez le système pour appliquer tous les changements"
echo "2. Copiez le proxy optimisé dans /opt/redis-proxy/"
echo "3. Démarrez le service: systemctl start redis-proxy"
echo "4. Monitoring: proxy-monitor"
echo ""
echo "🔍 VÉRIFICATIONS:"
echo "- File descriptors: ulimit -n (doit être 1048576)"
echo "- Paramètres réseau: sysctl net.core.somaxconn"
echo "- Service Redis: systemctl status redis"
echo ""
echo "⚠️  IMPORTANT: Redémarrage système recommandé"