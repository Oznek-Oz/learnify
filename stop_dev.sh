#!/bin/bash
# stop_dev.sh — Arrêter tous les services démarrés par run_dev.sh

echo "🛑 Arrêt des services Learnify..."

# Fonction pour arrêter un service
stop_service() {
    local name="$1"
    local pid_file="${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Arrêt $name (PID: $pid)..."
            kill "$pid"
            sleep 2

            # Force kill si nécessaire
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚠️  Force kill $name..."
                kill -9 "$pid" 2>/dev/null
            fi
        else
            echo "ℹ️  $name déjà arrêté"
        fi
        rm -f "$pid_file"
    else
        echo "ℹ️  PID file $pid_file introuvable"
    fi
}

# Arrêter dans l'ordre inverse
stop_service "flower"
stop_service "worker_generation"
stop_service "worker_courses"
stop_service "django"

# Arrêter Redis si on l'a démarré
if pgrep -x "redis-server" > /dev/null; then
    echo "🔄 Arrêt Redis..."
    pkill redis-server
fi

echo "✅ Tous les services arrêtés"
echo "🧹 Nettoyage des fichiers PID..."
rm -f *.pid

echo ""
echo "💡 Pour redémarrer : ./run_dev.sh"