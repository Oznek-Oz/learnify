# Test de l'application `quiz_game`

Ce document explique comment tester l'application `quiz_game` localement et via les tests unitaires.

## Prérequis

- Avoir activé l'environnement virtuel du projet.
- Avoir exécuté les migrations :

```bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

- Les 10 niveaux sont créés **automatiquement** lors de la création d'une progression (pas besoin de les créer manuellement).

## Lancer les tests unitaires

Pour exécuter seulement les tests de `quiz_game` :

```bash
python manage.py test quiz_game
```

Pour exécuter l'ensemble des tests :

```bash
python manage.py test
```

## Génération automatique des niveaux et quiz

### Workflow

1. L'utilisateur crée/récupère une progression pour un cours + thématique
2. La méthode `ensure_initialized()` est appelée automatiquement
3. Les 10 niveaux sont créés (s'ils n'existent pas)
4. Un `LevelProgress` est créé pour chaque niveau avec le statut `GENERATING`
5. Une tâche Celery `generate_level_quizzes_task` est lancée en arrière-plan pour générer les quiz de chaque niveau
6. Les quiz sont générés via Gemini en utilisant la RAG (recherche sémantique sur le contenu du cours)
7. Une fois terminée, le statut du niveau passe à `READY`

### API Endpoints à tester manuellement

Préfixe : `/api/quiz-game/`

#### 1. Initialiser / récupérer la progression

**POST** `/api/quiz-game/progress/` (ou GET avec query params)

Payload type JSON :

```json
{
  "course_id": 1,
  "topic": "Introduction aux mathématiques"   
}
```

Réponse : objet `QuizGameProgress` contenant `unlocked_levels` (tableau des niveaux débloqués), `completed_levels`, et `level_progresses` (l'état de chaque niveau).

**Exemple de réponse** :

```json
{
  "id": 1,
  "course": 1,
  "course_title": "Test Course",
  "topic": "Introduction aux mathématiques",
  "unlocked_levels": [
    {"id": 1, "number": 1, "title": "Niveau 1 - Débutant", "difficulty": "easy", "quiz_count": 5}
  ],
  "completed_levels": [],
  "level_progresses": [
    {
      "id": 1,
      "level": {...},
      "status": "generating",  // ou "ready", "in_progress", "passed", "failed"
      "completed_quiz_count": 0,
      "required_quiz_count": 5,
      "generated_questions": 0,
      "score": 0,
      "unlocked_at": null,
      "completed_at": null
    },
    ...dix niveaux en total...
  ],
  "created_at": "2026-06-04T...",
  "updated_at": "2026-06-04T..."
}
```

#### 2. Lister les niveaux

**GET** `/api/quiz-game/levels/`

Réponse : liste de tous les 10 niveaux disponibles avec leurs métadonnées.

#### 3. Démarrer un niveau

**POST** `/api/quiz-game/levels/<number>/start/`

Payload :

```json
{ "course_id": 1, "topic": "Introduction aux mathématiques" }
```

Réponse : état `LevelProgress` du niveau.

**Nota** : Si le niveau est en statut `GENERATING`, la réponse aura le code **202 Accepted**, indiquant que les quiz sont encore en cours de génération.

#### 4. Soumettre un niveau (validation)

**POST** `/api/quiz-game/levels/<number>/submit/`

Payload :

```json
{
  "course_id": 1,
  "topic": "Introduction aux mathématiques",
  "completed_quiz_count": 5,
  "score": "100.00",
  "passed": true
}
```

Réponse : progression mise à jour (les niveaux suivants sont débloqués si la soumission est réussie).

## Authentification

Les endpoints nécessitent un utilisateur authentifié. Vous pouvez :

- Utiliser l'API d'authentification existante : `POST /api/auth/login/` pour récupérer le `access` token (JWT), puis ajouter l'en-tête :

```
Authorization: Bearer <ACCESS_TOKEN>
```

- Ou tester via l'admin Django si nécessaire.

## Exemple `curl` (login + init progress)

1. Obtenir le token :

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com","password":"pass"}'
```

Réponse :

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

2. Initialiser la progression (les 10 niveaux seront créés et les quiz générés) :

```bash
curl -X POST http://127.0.0.1:8000/api/quiz-game/progress/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"course_id": 1, "topic": "Introduction aux mathématiques"}'
```

3. Vérifier le statut de génération :

```bash
curl -X GET "http://127.0.0.1:8000/api/quiz-game/progress/?course_id=1&topic=Introduction%20aux%20math%C3%A9matiques" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Vérifiez le champ `status` de chaque `level_progress` : il passera de `GENERATING` à `READY` une fois que Celery aura généré les quiz.

4. Démarrer le niveau 1 (une fois prêt) :

```bash
curl -X POST http://127.0.0.1:8000/api/quiz-game/levels/1/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"course_id": 1, "topic": "Introduction aux mathématiques"}'
```

5. Soumettre le niveau 1 (validation) :

```bash
curl -X POST http://127.0.0.1:8000/api/quiz-game/levels/1/submit/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"course_id": 1, "topic": "Introduction aux mathématiques", "completed_quiz_count": 5, "score": "100.00", "passed": true}'
```

Après validation, les niveaux 2 et 3 seront automatiquement débloqués.

## Notes de debugging

- **Celery non disponible** : Si Celery n'est pas en cours d'exécution, les quiz ne seront pas générés. Vérifiez que le worker Celery est lancé : `celery -A config worker -l info -Q generation`.
- **Pas de chunks trouvés** : Assurez-vous que le cours est dans le statut `READY` et que son contenu a été traité (embeddings créés dans ChromaDB).
- **Timeout de génération** : Si la génération Gemini est lente, le statut restera `GENERATING` plus longtemps. Vous pouvez suivre les logs Celery.


