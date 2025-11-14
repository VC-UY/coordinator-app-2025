#!/bin/bash

# Script pour visualiser les logs du Coordinator

LOGS_DIR="coordinator_project/logs"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📊 Visualisation des logs du Coordinator${NC}"
echo ""

# Vérifier si le répertoire de logs existe
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}⚠️  Le répertoire de logs n'existe pas encore${NC}"
    echo "   Les logs seront créés au premier démarrage"
    exit 0
fi

# Menu
echo "Choisissez les logs à visualiser:"
echo "  1) Django (derniers)"
echo "  2) Proxy (derniers)"
echo "  3) Les deux côte à côte (tmux requis)"
echo "  4) Tous les logs disponibles"
echo "  5) Quitter"
echo ""
read -p "Votre choix (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}📄 Logs Django:${NC}"
        if [ -f "$LOGS_DIR/django_latest.log" ]; then
            tail -f "$LOGS_DIR/django_latest.log"
        else
            echo -e "${YELLOW}⚠️  Aucun log Django trouvé${NC}"
        fi
        ;;
    2)
        echo -e "${BLUE}📄 Logs Proxy:${NC}"
        if [ -f "$LOGS_DIR/proxy_latest.log" ]; then
            tail -f "$LOGS_DIR/proxy_latest.log"
        else
            echo -e "${YELLOW}⚠️  Aucun log Proxy trouvé${NC}"
        fi
        ;;
    3)
        if ! command -v tmux &> /dev/null; then
            echo -e "${YELLOW}⚠️  tmux n'est pas installé${NC}"
            echo "   Installation: sudo apt-get install tmux"
            exit 1
        fi
        
        if [ ! -f "$LOGS_DIR/django_latest.log" ] || [ ! -f "$LOGS_DIR/proxy_latest.log" ]; then
            echo -e "${YELLOW}⚠️  Les logs ne sont pas encore disponibles${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}📊 Logs en parallèle (tmux)${NC}"
        echo "   Panneau gauche: Proxy"
        echo "   Panneau droit: Django"
        echo ""
        echo "   Ctrl+B puis flèches pour naviguer"
        echo "   Ctrl+B puis d pour détacher"
        echo ""
        
        tmux new-session \; \
          split-window -h \; \
          send-keys "tail -f $LOGS_DIR/proxy_latest.log" C-m \; \
          select-pane -t 1 \; \
          send-keys "tail -f $LOGS_DIR/django_latest.log" C-m \; \
          select-pane -t 0
        ;;
    4)
        echo -e "${BLUE}📁 Logs disponibles:${NC}"
        echo ""
        ls -lh "$LOGS_DIR"/*.log 2>/dev/null || echo "Aucun log trouvé"
        ;;
    5)
        echo "Au revoir!"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}⚠️  Choix invalide${NC}"
        exit 1
        ;;
esac
