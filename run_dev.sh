#!/bin/bash

# run_dev.sh — Script pour démarrer tous les services Learnify

echo "🚀 Démarrage des services Learnify..."

PROJECT_DIR="/home/kenz/projects/learnify"

# Vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Vérifier les prérequis
if ! command_exists redis-server; then
    echo "❌ Redis n'est pas installé."
    echo "Installe-le avec : sudo apt install redis-server"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python n'est pas installé."
    exit 1
fi

# Créer le dossier des logs
mkdir -p logs

# Démarrer Redis si nécessaire
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔄 Démarrage Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis OK"

# Fonction de démarrage d'un service
start_service() {
    local name="$1"
    local command="$2"
    local log_file="logs/${name}.log"

    echo ""
    echo "🔄 Démarrage $name..."
    echo "Commande : $command"

    nohup bash -c "
        cd '$PROJECT_DIR' || exit 1
        $command
    " > "$log_file" 2>&1 &

    local pid=$!
    echo "$pid" > "${name}.pid"

    sleep 3

    if kill -0 "$pid" 2>/dev/null; then
        echo "✅ $name démarré (PID: $pid)"
        echo "📄 Logs : $log_file"
    else
        echo "❌ Échec du démarrage de $name"
        echo ""
        echo "===== LOGS ====="
        cat "$log_file"
        echo "================"
        exit 1
    fi
}

# Django
start_service "django" \
"source venv/bin/activate && python manage.py runserver"

# Worker Celery - Courses
start_service "worker_courses" \
"source venv/bin/activate && celery -A config worker -Q courses --pool=prefork --concurrency=2 -n worker_courses@%h --loglevel=info"

# Worker Celery - Generation
start_service "worker_generation" \
"source venv/bin/activate && celery -A config worker -Q generation --pool=threads --concurrency=4 -n worker_generation@%h --loglevel=info"

# Flower (optionnel)
if command_exists flower; then
    start_service "flower" \
    "source venv/bin/activate && celery -A config flower --port=5555"
fi

echo ""
echo "🎉 Tous les services sont démarrés !"
echo ""
echo "📊 Services actifs :"
echo "   🌐 Django : http://127.0.0.1:8000"

if command_exists flower; then
    echo "   🌸 Flower : http://127.0.0.1:5555"
fi

echo "   📁 Logs : ./logs/"
echo ""
echo "🛑 Pour arrêter les services :"
echo "   ./stop_dev.sh"
echo ""
echo "💡 Vérification :"
echo "   tail -f logs/django.log"
echo "   tail -f logs/worker_courses.log"
echo "   tail -f logs/worker_generation.log"