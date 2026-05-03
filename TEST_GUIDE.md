# 🧪 Guide de Test Rapide - Learnify

## 🚀 Démarrage Rapide

```bash
# Démarrer tous les services automatiquement
./run_dev.sh

# Ou manuellement dans 4 terminaux :
# Terminal 1: python manage.py runserver
# Terminal 2: celery -A config worker -Q courses --pool=prefork --concurrency=2 -n worker_courses@%h --loglevel=info
# Terminal 3: celery -A config worker -Q generation --pool=threads --concurrency=4 -n worker_generation@%h --loglevel=info
# Terminal 4: cd ../learnify-frontend && npm run dev
```

## ✅ Tests Fonctionnels

### 1. Authentification
```bash
# Créer un utilisateur de test
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test123"}'

# Se connecter
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
# Note le token JWT retourné
```

### 2. Upload de Cours (avec throttling)
```bash
# Upload un PDF (remplace TOKEN par le vrai token)
curl -X POST http://127.0.0.1:8000/api/courses/ \
  -H "Authorization: Bearer TOKEN" \
  -F "title=Test Course" \
  -F "description=Cours de test" \
  -F "file=@/path/to/your/test.pdf"

# Test throttling (essaie plusieurs fois rapidement)
# Doit retourner 429 après 5 uploads/heure
```

### 3. Pagination
```bash
# Liste des cours avec pagination
curl "http://127.0.0.1:8000/api/courses/?page=1&page_size=10" \
  -H "Authorization: Bearer TOKEN"

# Liste des flashcards (pagination large)
curl "http://127.0.0.1:8000/api/flashcards/?page=1&page_size=50" \
  -H "Authorization: Bearer TOKEN"
```

### 4. Génération avec Fallback
```bash
# Générer des flashcards
curl -X POST http://127.0.0.1:8000/api/flashcards/generate/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "topic": "machine learning",
    "num_cards": 5
  }'

# Test fallback: coupe temporairement GEMINI_API_KEY dans .env
# La génération doit quand même réussir avec du contenu dégradé
```

### 5. Cache Redis
```bash
# Première recherche (calcule les embeddings)
curl -X POST http://127.0.0.1:8000/api/courses/1/search/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "algorithmes de classification"}'

# Seconde recherche identique (doit être instantanée grâce au cache)
curl -X POST http://127.0.0.1:8000/api/courses/1/search/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "algorithmes de classification"}'
```

### 6. Monitoring Celery
```bash
# Vérifier les workers actifs
curl http://127.0.0.1:5555/api/workers

# Vérifier les tâches en cours
curl http://127.0.0.1:5555/api/tasks

# Vérifier les statistiques
curl http://127.0.0.1:5555/api/stats
```

## 🔍 Tests de Performance

### Cache Effectiveness
```bash
# Mesurer le temps de réponse avec curl
time curl -X POST http://127.0.0.1:8000/api/courses/1/search/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "intelligence artificielle"}' \
  -o /dev/null -s
```

### Memory Usage
```bash
# Surveiller la mémoire des workers
watch -n 1 'ps aux | grep celery'
```

## 🛑 Arrêt des Services

```bash
# Arrêter automatiquement
./stop_dev.sh

# Ou manuellement :
# Ctrl+C dans chaque terminal
# pkill -f "celery.*worker"
# pkill -f "python.*runserver"
```

## 📊 Métriques à Vérifier

- **Pagination**: Réponses contiennent `count`, `next`, `previous`
- **Throttling**: Code 429 après dépassement limites
- **Cache**: Temps de réponse divisé par 10+ sur requêtes répétées
- **Fallback**: Succès même avec clé Gemini invalide
- **Timeouts**: Tâches Celery ne dépassent pas 10min (courses) / 5min (génération)
- **Workers**: Séparation courses (prefork) vs génération (threads)

## 🚨 Dépannage

### Problèmes Courants

**Erreur Redis**: `redis-server --daemonize yes`
**Erreur DB**: Vérifier PostgreSQL + migrations
**Erreur Celery**: Vérifier queues `courses` et `generation`
**Erreur Gemini**: Vérifier clé API + quota Google Cloud

### Logs à Consulter

```bash
# Logs Django
tail -f logs/django.log

# Logs Celery
tail -f logs/worker_courses.log
tail -f logs/worker_generation.log

# Logs Redis (si local)
redis-cli monitor
```