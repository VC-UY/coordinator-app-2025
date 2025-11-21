#!/bin/bash

# Script de démarrage rapide du Coordinator
# Lance Django et le Proxy Redis avec logs séparés

echo "🚀 Démarrage du Coordinator..."
echo ""

cd "$(dirname "$0")/coordinator_project"

# Vérifier que manage.py existe
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py introuvable"
    echo "   Assurez-vous d'être dans le bon répertoire"
    exit 1
fi

# Démarrer tous les services
python manage.py runall "$@"
