# 🚀 Proxy de Fichiers via Coordinator (BIDIRECTIONNEL)

## Architecture de Routage

Ce système résout le problème de communication entre Manager et Volontaire lorsqu'ils sont sur des sous-réseaux différents ou derrière des NAT.

**⚡ NOUVEAU :** Support bidirectionnel complet - routage des fichiers d'entrée ET de sortie !

```
┌─────────────────────────────────────────────────────────────────┐
│                   FLUX DE COMMUNICATION                          │
└─────────────────────────────────────────────────────────────────┘

1️⃣ Volontaire termine une tâche
   ↓
   Envoie: PUBLISH task/status {
       "task_id": "123",
       "status": "completed",
       "file_server": {
           "host": "192.168.1.100",  ← IP locale (non routable)
           "port": 5000
       }
   }

2️⃣ Coordinator intercepte le message
   ↓
   - Enregistre la tâche dans le proxy de fichiers
   - Remplace l'IP locale par l'IP du coordinator
   ↓
   Transmet: PUBLISH task/status {
       "task_id": "123",
       "status": "completed",
       "file_server": {
           "host": "10.0.0.50",      ← IP du coordinator (routable)
           "port": 8000,              ← Port du proxy HTTP
           "path": "/files/123/"
       }
   }

3️⃣ Manager reçoit le message
   ↓
   Télécharge: GET http://10.0.0.50:8000/files/123/result.txt

4️⃣ Coordinator reçoit la requête HTTP
   ↓
   Route vers: GET http://192.168.1.100:5000/files/result.txt
   ↓
   Retourne le fichier au Manager

5️⃣ Manager envoie task/terminate
   ↓
   Coordinator nettoie la tâche du registre
```

## Configuration

### Coordinator

Le proxy démarre automatiquement deux services:
- **Port 6380**: Proxy Redis (messages)
- **Port 8000**: Proxy HTTP (fichiers)

### Volontaire

Aucune modification nécessaire ! Le volontaire continue d'envoyer son IP locale.

### Manager

Le manager reçoit automatiquement l'URL du coordinator et télécharge via HTTP:

```python
# Dans le handler de task/status
file_server = message_data.get('file_server', {})
host = file_server.get('host')  # IP du coordinator
port = file_server.get('port')  # 8000
path = file_server.get('path')  # /files/123/
files = file_server.get('output_files', [])

# Télécharger un fichier
for filename in files:
    url = f"http://{host}:{port}{path}{filename}"
    response = requests.get(url)
    # Sauvegarder le fichier
```

## API du Proxy de Fichiers

### GET /files/{task_id}/{filename}

Télécharge un fichier de résultat.

**Exemple:**
```bash
curl http://coordinator:8000/files/task_123/result.txt
```

**Réponse:**
- `200 OK`: Fichier téléchargé
- `404 Not Found`: Tâche non enregistrée
- `502 Bad Gateway`: Impossible de contacter le volontaire
- `504 Gateway Timeout`: Timeout du volontaire

**Headers:**
- `X-Routed-By: Coordinator-File-Proxy`
- `X-Volunteer-Id: volunteer_456`

### GET /health

Vérification de santé du proxy.

**Réponse:**
```json
{
  "status": "healthy",
  "uptime": 3600.5,
  "registered_tasks": 42
}
```

### GET /stats

Statistiques du proxy.

**Réponse:**
```json
{
  "stats": {
    "total_requests": 1234,
    "successful_transfers": 1200,
    "failed_transfers": 34,
    "bytes_transferred": 1048576000
  },
  "registered_tasks": 42,
  "tasks": ["task_123", "task_456", ...]
}
```

### POST /register_task

Enregistre manuellement une tâche (utilisé en interne).

**Body:**
```json
{
  "task_id": "task_123",
  "volunteer_ip": "192.168.1.100",
  "volunteer_port": 5000,
  "volunteer_id": "volunteer_456"
}
```

### DELETE /unregister_task/{task_id}

Désenregistre une tâche.

**Exemple:**
```bash
curl -X DELETE http://coordinator:8000/unregister_task/task_123
```

## Avantages

✅ **Transparent**: Aucune modification côté Volontaire ou Manager
✅ **Sécurisé**: Le Volontaire n'expose pas son IP publique
✅ **Compatible NAT**: Fonctionne derrière des NAT/Firewalls
✅ **Multi-sous-réseaux**: Fonctionne entre sous-réseaux différents
✅ **Évolutif**: Supporte des milliers de tâches simultanées
✅ **Observable**: Statistiques et monitoring intégrés

## 🆕 Routage Bidirectionnel (Nouvelle Fonctionnalité)

### Fichiers d'Entrée (Manager → Volontaire)

Le proxy intercepte maintenant aussi les messages `task/assignment` pour router les fichiers d'entrée :

```
Manager envoie task/assignment avec :
{
  "input_data": {
    "file_server": {
      "host": "192.168.2.50",  ← IP locale Manager
      "port": 8080
    }
  }
}

↓ Proxy intercepte et transforme ↓

Volontaire reçoit :
{
  "input_data": {
    "file_server": {
      "host": "coordinator.example.com",  ← IP publique Coordinator
      "port": 8410,
      "path": "/files/input_<workflow_id>/"
    }
  }
}
```

**Mapping enregistré :**
- `input_<workflow_id>` → `192.168.2.50:8080`

**Téléchargement Volontaire :**
```bash
curl http://coordinator:8410/files/input_<workflow_id>/scenario.xml
# → Routé vers http://192.168.2.50:8080/scenario.xml
```

### Résumé des Flux

| Direction | Canal | Transformateur | Mapping |
|-----------|-------|---------------|---------|
| Manager → Volontaire | `task/assignment` | `route_input_files()` | `input_<workflow_id>` |
| Volontaire → Manager | `task/status` | `route_file_server()` | `<task_id>` |

## Limitations

⚠️ **Bande passante**: Tous les fichiers passent par le coordinator
⚠️ **Latence**: Une étape de routage supplémentaire
⚠️ **SPOF**: Le coordinator devient un point de défaillance unique

## Optimisations Futures

1. **Cache**: Mettre en cache les fichiers fréquemment demandés
2. **Compression**: Compresser les fichiers à la volée
3. **Streaming**: Stream les gros fichiers sans les charger en mémoire
4. **Load Balancing**: Plusieurs coordinators pour la haute disponibilité
5. **P2P Fallback**: Essayer la connexion directe, fallback sur routage
