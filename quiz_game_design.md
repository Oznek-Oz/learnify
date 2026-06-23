# Nouvelle application Django : `quiz_game`

## Objectif

Créer une application de type "jeu d'étude" indépendante des applications existantes `quizz` et `flashcards`.
Cette application permet à un utilisateur de progresser sur 10 cases/niveaux, avec déverrouillage progressif et une difficulté croissante.

## Principes de progression

- Il y a 10 cases (niveaux) numérotées de 1 à 10.
- À l'état initial, seule la case 1 est accessible.
- Lorsqu'un utilisateur valide le niveau N, les niveaux N+1 et N+2 sont débloqués.
- Un maximum de 5 niveaux peuvent être débloqués en même temps.
- La difficulté augmente du niveau 1 au niveau 10.
- Le nombre de quiz augmente également :
  - niveau 1 → 5 quiz
  - niveau 10 → 20 quiz
  - les niveaux intermédiaires suivent une progression croissante.

## Architecture de l'application

### Nom de l'application

- Nom Django : `quiz_game`
- Dossier racine : `/home/kenz/projects/learnify/quiz_game`

### Isolation et intégration

- L'application sera autonome et ne modifiera pas la logique existante des apps `quizz` ou `flashcards`.
- Elle pourra réutiliser le modèle `Course` pour lier la progression à un cours ou à une thématique.
- L'intégration se fera via :
  - `INSTALLED_APPS += ['quiz_game']`
  - `path('api/quiz-game/', include('quiz_game.urls'))` dans `config/urls.py`

## Initialisation automatique de la progression

Lors de la création/récupération d'une progression, la méthode `ensure_initialized()` est appelée automatiquement. Elle :

1. **Crée les 10 niveaux** (s'ils n'existent pas encore globalement) avec la configuration LEVEL_CONFIG :
   - Niveau 1-3 : easy (5, 7, 9 quiz)
   - Niveau 4-7 : medium (11, 13, 15, 16 quiz)
   - Niveau 8-10 : hard (17, 18, 20 quiz)

2. **Crée les LevelProgress** pour chaque niveau avec le statut `GENERATING`

3. **Lance des tâches Celery** en arrière-plan (`generate_level_quizzes_task`) pour générer les quiz de chaque niveau

### Génération des quiz

Les quiz sont générés via la tâche Celery `generate_level_quizzes_task`, qui :

1. Recherche les chunks pertinents du cours via ChromaDB (RAG search)
2. Utilise Gemini pour générer les questions selon :
   - La difficulté du niveau
   - Le nombre de quiz requis
   - La thématique / topic spécifiée
3. Stocke le nombre de questions générées et passe le statut à `READY`

En cas d'erreur ou de timeout, le statut reste `FAILED` et l'utilisateur peut relancer la génération.

### Modèle `Level`

Représente les 10 cases du parcours.

Champs proposés :
- `number` (int, unique, 1..10)
- `title` (char)
- `difficulty` (char ou int)
- `quiz_count` (int)
- `description` (text)
- `is_active` (bool) si l'on veut activer/désactiver un niveau globalement

### Modèle `QuizGameProgress`

Stocke l'état global de progression de l'utilisateur pour un cours/une thématique.

Champs proposés :
- `user` → ForeignKey vers `users.CustomUser`
- `course` → ForeignKey vers `courses.Course`
- `topic` → char, optionnel si le jeu est lié à un thème spécifique
- `current_level` → int ou ForeignKey vers `Level`
- `unlocked_levels` → liste ou relation vers `Level` (via `ManyToManyField`)
- `completed_levels` → liste ou relation vers `Level`
- `max_unlocked` → int (toujours <= 5)
- `last_seen` / `updated_at`

### Modèle `LevelProgress`

Stocke l'état propre à chaque niveau pour un utilisateur.

Champs proposés :
- `progress` → `pending`, `generating`, `ready`, `in_progress`, `passed`, `failed`
- `level` → ForeignKey vers `Level`
- `user_progress` → ForeignKey vers `QuizGameProgress`
- `completed_quiz_count` → int
- `required_quiz_count` → int
- `generated_questions` → int (nombre de questions générées par Gemini)
- `score` → float/int
- `unlocked_at`, `completed_at`

**Workflow** :
1. Créé automatiquement lors de l'initialisation avec `status = GENERATING`
2. Celery lance la génération des quiz en arrière-plan
3. Une fois Gemini a généré les questions, `status = READY`
4. Quand l'utilisateur start le niveau, `status = IN_PROGRESS`
5. À la soumission réussie, `status = PASSED`

### Modèle `LevelQuiz`

Permet de stocker ou générer les quiz d'un niveau.

Champs proposés :
- `level` → ForeignKey vers `Level`
- `title` → char
- `question_count` → int
- `difficulty` → char
- `status` → pending / ready / completed
- `quiz_data` ou relation vers des questions si on stocke les questions.

## Règles de déverrouillage

- Initialisation :
  - seul le niveau 1 est `unlocked`.
  - `completed_levels` est vide.
- Validation du niveau N :
  - marquer le niveau N comme `passed`
  - ajouter N à `completed_levels`
  - déverrouiller N+1 et N+2 si existants
  - si plus de 5 niveaux seraient déverrouillés, conserver le premier niveau complété ou le plus ancien, pour garder 5 niveaux ouverts.
- Exemple :
  - départ : [1]
  - après validation de 1 : [1, 2, 3]
  - après validation de 2 : [1, 2, 3, 4, 5] (max 5 débloqués)
  - après validation de 3 : [1, 2, 3, 4, 5, 6, 7] -> on garde 5 débloqués actifs, par exemple [3, 4, 5, 6, 7] ou selon règle métier choisie.

## Progression des difficulties et du nombre de quiz

### Difficulté

- Le niveau 1 commence facile.
- Le niveau 10 est le plus difficile.
- Les niveaux peuvent être mappés ainsi :
  - 1-3 : easy / facile
  - 4-7 : medium / moyen
  - 8-10 : hard / difficile

### Nombre de quiz

Proposition de progression croissante :

- Niveau 1 : 5 quiz
- Niveau 2 : 7 quiz
- Niveau 3 : 9 quiz
- Niveau 4 : 11 quiz
- Niveau 5 : 13 quiz
- Niveau 6 : 15 quiz
- Niveau 7 : 16 quiz
- Niveau 8 : 17 quiz
- Niveau 9 : 18 quiz
- Niveau 10 : 20 quiz

Ces valeurs peuvent être ajustées dans des constantes de configuration.

## API proposées

### Préfixe

- `/api/quiz-game/`

### Endpoints principaux

- `GET /api/quiz-game/progress/`
  - renvoie la progression de l'utilisateur pour un cours/thème donné
  - inclut les niveaux débloqués, les niveaux complétés, l'état de chaque niveau

- `POST /api/quiz-game/progress/`
  - crée ou met à jour une progression pour un utilisateur + cours
  - permet de définir le topic / la course active

- `GET /api/quiz-game/levels/`
  - liste tous les niveaux disponibles et leurs métadonnées (difficulty, quiz_count)

- `GET /api/quiz-game/levels/<int:level_number>/`
  - détail d’un niveau, état du niveau pour l’utilisateur

- `POST /api/quiz-game/levels/<int:level_number>/start/`
  - démarre un niveau si débloqué

- `POST /api/quiz-game/levels/<int:level_number>/submit/`
  - soumet les résultats du niveau et déclenche le déverrouillage des niveaux suivants

- `GET /api/quiz-game/levels/<int:level_number>/quizzes/`
  - liste des quiz du niveau

### Gestion des validations

- `POST /api/quiz-game/levels/<int:level_number>/submit/`
  - attend un payload de score ou d'état de quiz
  - si niveau validé, passe à `passed` et déverrouille les niveaux suivants
  - si échoué, reste bloqué sur le niveau actuel

## Utilisation des modèles existants

- Réutiliser `Course` de `courses.models` comme référence de cours.
- Ne pas modifier les modèles ou vues de `quizz`.
- Le nouveau module est bien séparé dans `quiz_game/`.

## Configuration Django

- Ajouter `quiz_game` à `INSTALLED_APPS` dans `config/settings.py`. ✅ Fait
- Ajouter l'URL de routage dans `config/urls.py` : ✅ Fait
  - `path('api/quiz-game/', include('quiz_game.urls'))`
- Ajouter les constantes dans `config/app_config.py` : ✅ Fait
  - `QUIZ_GAME_LEVELS = 10`
  - `QUIZ_GAME_MIN_QUIZZES = 5`
  - `QUIZ_GAME_MAX_QUIZZES = 20`
  - `QUIZ_GAME_MAX_UNLOCKED_LEVELS = 5`

### Lancer les workers Celery

Pour que la génération automatique des quiz fonctionne, les workers Celery doivent être en cours d'exécution :

```bash
# Worker pour la queue 'generation'
celery -A config worker -l info -Q generation
```

## Sécurité et permissions

- Toutes les routes doivent être protégées par `IsAuthenticated`.
- Les données de progression doivent toujours être filtrées par `request.user`.
- Les actions sur un `course` doivent vérifier que l'utilisateur est propriétaire du cours.

## Commerce et futur

- L’application peut évoluer vers un système de récompense ou des objectifs quotidiens.
- La progression peut être enrichie par un mode thématique multi-cours.
- On pourra ajouter des métriques de performance (`best_score`, `time_spent`, `accuracy`).

## Conclusion

Cette version de `quiz_game` permet de conserver la logique `quizz` existante telle qu’elle est, tout en ajoutant un parcours gamifié indépendant.
Le design reste simple, modulaire, et conforme aux conventions déjà en place dans le projet.
