# 🚀 Guide de Démarrage Simplifié

## Lancement Ultra-Rapide

```bash
./start.sh
```

**C'est tout !** 🎉

Cette unique commande démarre automatiquement :
- ✅ Serveur Django (port 8080)
- ✅ Proxy Redis (port 6380)  
- ✅ Proxy de fichiers (port 8000)

Les logs sont séparés automatiquement dans `coordinator_project/logs/`

---

## 📊 Voir les Logs en Temps Réel

```bash
./view_logs.sh
```

Menu interactif :
1. Logs Django
2. Logs Proxy
3. Les deux côte à côte
4. Liste de tous les logs

---

## Options Avancées

```bash
# Personnaliser les ports
cd coordinator_project
python manage.py runall --django-port 9000 --proxy-port 7000

# Voir toutes les options
python manage.py runall --help
```

---

## 🛑 Arrêter les Services

Dans le terminal où tournent les services :
```
Ctrl+C
```

---

## 📝 Fichiers de Logs

```
coordinator_project/logs/
├── django_latest.log     # Django (temps réel)
├── proxy_latest.log      # Proxy (temps réel)
├── django_YYYYMMDD_HHMMSS.log  # Archives
└── proxy_YYYYMMDD_HHMMSS.log   # Archives
```

Visualiser :
```bash
tail -f coordinator_project/logs/django_latest.log
tail -f coordinator_project/logs/proxy_latest.log
```

---

## ✅ Vérification Rapide

```bash
# Serveur Django
curl http://localhost:8080/

# Proxy de fichiers
curl http://localhost:8000/health

# Proxy Redis
redis-cli -h localhost -p 6380 PING
```

---

## 📚 Documentation Complète

- **Détails complets** : [coordinator_project/QUICK_START.md](coordinator_project/QUICK_START.md)
- **Proxy de fichiers** : [FILE_PROXY_GUIDE.md](FILE_PROXY_GUIDE.md)
- **Architecture générale** : [README.md](README.md)

---

**Questions ?** Consultez les logs ou la documentation complète !
