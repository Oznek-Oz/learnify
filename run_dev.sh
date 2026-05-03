#!/bin/bash
# run_dev.sh — Script pour démarrer tous les services en développement

echo "🚀 Démarrage des services Learnify..."

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Vérifier les prérequis
if ! command_exists redis-server; then
    echo "❌ Redis n'est pas installé. Installe-le avec : sudo apt install redis-server"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python n'est pas installé."
    exit 1
fi

# Créer le répertoire logs s'il n'existe pas
mkdir -p logs

# Démarrer Redis en arrière-plan si pas déjà lancé
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔄 Démarrage Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis OK"

# Fonction pour démarrer un service en arrière-plan
start_service() {
    local name="$1"
    echo "Name= $name"
    local command="$2"
    echo "command= $command"
    local log_file="logs/${name}.log"

    echo "🔄 Démarrage $name..."
    nohup $command > "$log_file" 2>&1 &
    echo $! > "${name}.pid"
    sleep 2

    if kill -0 $(cat "${name}.pid") 2>/dev/null; then
        echo "✅ $name démarré (PID: $(cat ${name}.pid))"
        echo "   📄 Logs: $log_file"
    else
        echo "❌ Échec démarrage $name"
        cat "$log_file"
        exit 1
    fi
}

# Terminal 1 — Django
start_service "django" "bash -c \"cd /home/kenz/projects/learnify && python3 manage.py runserver\""

# Terminal 2 — Worker courses (CPU intensif)
start_service "worker_courses" "bash -c \"cd /home/kenz/projects/learnify && celery -A config worker -Q courses --pool=prefork --concurrency=2 -n worker_courses@%h --loglevel=info\""

# Terminal 3 — Worker generation (I/O intensif)
start_service "worker_generation" "bash -c \"cd /home/kenz/projects/learnify && celery -A config worker -Q generation --pool=threads --concurrency=4 -n worker_generation@%h --loglevel=info\""

# Terminal 4 — Flower (optionnel)
if command_exists flower; then
    start_service "flower" "bash -c \"cd /home/kenz/projects/learnify && celery -A config flower --port=5555\""
fi

echo ""
echo "🎉 Tous les services sont démarrés !"
echo ""
echo "📊 Services actifs :"
echo "   🌐 Django:    http://127.0.0.1:8000"
echo "   📊 Flower:    http://127.0.0.1:5555 (si activé)"
echo "   📁 Logs:      ./logs/"
echo ""
echo "🛑 Pour arrêter : ./stop_dev.sh"
echo ""
echo "💡 Tests à faire :"
echo "   - Upload PDF:    curl -X POST http://127.0.0.1:8000/api/courses/"
echo "   - Générer quiz:  curl -X POST http://127.0.0.1:8000/api/quiz/generate/"
echo "   - Pagination:    curl http://127.0.0.1:8000/api/flashcards/?page=1"