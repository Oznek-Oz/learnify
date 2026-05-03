# Description du fonctionnement du système Learnify

Ce document décrit le flux d'utilisation côté serveur lorsque :
- un utilisateur upload un document PDF,
- un utilisateur génère un quiz,
- un utilisateur génère des flashcards.

Il explique aussi comment le traitement est réparti quand plusieurs utilisateurs agissent en même temps.

---

## 1. Upload d'un document PDF

### 1.1. Ce que fait l'utilisateur

1. L'utilisateur authentifié charge un fichier via l'endpoint `POST /api/courses/`.
2. Le fichier est transmis au backend Django.
3. Le backend enregistre le fichier dans `MEDIA_ROOT` via le modèle `courses.models.Course`.

### 1.2. Ce que fait le backend immédiatement

- `courses/views.py` → `CourseListCreateView.perform_create()` :
  - sauvegarde le `Course` avec `owner=request.user`.
  - déclenche `process_course.delay(course.id)` pour traiter le cours en arrière-plan.
- Le document est donc uploadé très rapidement et l'utilisateur ne bloque pas sur le traitement.

### 1.3. Traitement asynchrone du document

Le traitement asynchrone est géré par Celery dans `courses/tasks.py`.

1. La tâche `process_course` récupère le `Course` par `course_id`.
2. Elle passe le statut du cours à `processing`.
3. Elle lit le fichier depuis `course.file.path`.
4. Selon le type de fichier :
   - PDF → `extract_text_from_pdf()` dans `courses/services.py`
   - image → `extract_text_from_image()` (pour l'instant non activé)
5. Le texte est découpé en morceaux (`chunks`) avec `chunk_text_adaptive()`.
6. Les chunks sont enregistrés en base via `CourseChunk`.
7. Les embeddings sont calculés et stockés dans ChromaDB via `courses/vector_store.py`.
8. Le statut du `Course` passe à `ready` si tout réussit, ou à `failed` en cas d'erreur.

### 1.4. Répartition du travail si plusieurs uploads arrivent en même temps

- Les uploads sont acceptés rapidement par Django.
- Chaque upload crée une tâche Celery distincte : `process_course.delay(course.id)`.
- Celery utilise Redis comme broker (`config/settings.py` : `CELERY_BROKER_URL = 'redis://localhost:6379/0'`).
- Les tâches de cours sont envoyées sur la queue `courses`.
- Les workers Celery peuvent être dimensionnés pour traiter plusieurs tâches en parallèle.
- `CELERY_WORKER_PREFETCH_MULTIPLIER = 1` garantit qu'un worker prend une seule tâche à la fois, ce qui limite les blocages.
- Le système applique un throttle DRF côté backend : `CourseUploadThrottle` limite l'upload à `5/hour` par utilisateur.
- Si plusieurs utilisateurs uploadent simultanément, chaque tâche est indépendante :
  - extraction du texte et chunking sont faits par tâche,
  - les embeddings sont stockés dans une collection ChromaDB par `course_id`,
  - les statuts de cours sont isolés par utilisateur.

### 1.5. États possibles du cours

- `uploaded` → fichier reçu, traitement non démarré.
- `processing` → tâche Celery en cours.
- `ready` → document prêt, embeddings stockés, utilisable pour quiz/flashcards.
- `failed` → erreur ou fichier sans contenu extractible.

---

## 2. Génération de quiz

### 2.1. Ce que fait l'utilisateur

1. L'utilisateur soumet une requête `POST /api/quiz/generate/`.
2. Il fournit :
   - `course_id`,
   - `topic`,
   - `difficulty`,
   - `num_questions`.
3. Le backend renvoie immédiatement un quiz de statut `pending`.

### 2.2. Ce que fait le backend immédiatement

- `quizz/views.py` → `GenerateQuizView.post()` :
  1. vérifie que le cours appartient à l'utilisateur,
  2. vérifie que `course.status == ready`,
  3. récupère des chunks pertinents via `search_similar_chunks()` dans `courses/vector_store.py`,
  4. crée un objet `Quiz` avec `status = pending`,
  5. lance `generate_quiz_task.delay(...)` sur la queue `generation`,
  6. renvoie `202 Accepted`.

### 2.3. Traitement asynchrone du quiz

- `quizz/tasks.py` exécute `generate_quiz_task`.
- La tâche :
  1. met le quiz en `generating`,
  2. appelle `generate_quiz_from_chunks_safe()` dans `quizz/gemini_service.py`,
  3. crée les objets `Question` en base,
  4. met le quiz en `ready` si tout réussit,
  5. passe à `failed` en cas d'erreur ou de timeout.

### 2.4. Répartition du travail en cas de génération simultanée

- Les demandes de génération de quiz sont également mises en file d'attente Celery.
- Elles utilisent la queue `generation`.
- Un throttle `GenerationThrottle` limite les requêtes à `10/day` par utilisateur.
- Chaque quiz génère une tâche indépendante, ce qui permet à plusieurs utilisateurs de générer en parallèle sans bloquer le serveur HTTP.
- La queue `generation` est distincte de la queue `courses`, permettant de séparer le traitement CPU intensif du traitement I/O / API Gemini.

### 2.5. États possibles du quiz

- `pending` → quiz créé, génération en attente.
- `generating` → tâche Celery en cours.
- `ready` → quiz prêt, questions créées.
- `failed` → la génération a échoué.

---

## 3. Génération de flashcards

### 3.1. Ce que fait l'utilisateur

1. L'utilisateur soumet une requête `POST /api/flashcards/generate/`.
2. Il fournit :
   - `course_id`,
   - `topic`,
   - `num_cards`.
3. Le backend renvoie immédiatement un deck de statut `pending`.

### 3.2. Ce que fait le backend immédiatement

- `flashcards/views.py` → `GenerateFlashcardsView.post()` :
  1. vérifie que le cours appartient à l'utilisateur,
  2. vérifie que `course.status == ready`,
  3. récupère des chunks pertinents via `search_similar_chunks()`,
  4. crée un `FlashcardDeck` avec `status = pending`,
  5. lance `generate_flashcards_task.delay(...)` sur la queue `generation`,
  6. renvoie `202 Accepted`.

### 3.3. Traitement asynchrone des flashcards

- `flashcards/tasks.py` exécute `generate_flashcards_task`.
- La tâche :
  1. met le deck en `generating`,
  2. appelle `generate_flashcards_from_chunks_safe()` dans `flashcards/gemini_service.py`,
  3. crée les objets `Flashcard` en base,
  4. met le deck en `ready` si tout réussit,
  5. passe à `failed` en cas d'erreur.

### 3.4. Répartition du travail en cas de génération simultanée

- Comme pour les quiz, chaque demande de génération de flashcards devient une tâche Celery séparée.
- Le throttling `GenerationThrottle` protège contre les abus.
- Les tâches `generation` peuvent être traitées par plusieurs workers si le backend Celery est dimensionné en conséquence.
- Les recherches sémantiques utilisent les embeddings ChromaDB du cours et sont isolées par `course_id`.

### 3.5. États possibles du deck

- `pending` → deck créé, génération en attente.
- `generating` → tâche Celery en cours.
- `ready` → deck prêt, flashcards créées.
- `failed` → la génération a échoué.

---

## 4. Composants principaux

- `courses/views.py` : upload de cours et démarrage du pipeline.
- `courses/tasks.py` : extraction de texte, chunking, embeddings, stockage ChromaDB.
- `courses/services.py` : extraction et découpage adaptatif du texte.
- `courses/vector_store.py` : embeddings, ChromaDB, recherche sémantique.
- `flashcards/views.py` : création de deck et lancement de la génération.
- `flashcards/tasks.py` : génération asynchrone des flashcards.
- `quizz/views.py` : création de quiz et lancement de la génération.
- `quizz/tasks.py` : génération asynchrone des questions.
- `config/settings.py` : broker Redis, queues Celery, cache et throttles.
- `config/throttles.py` : limites d’usage côté utilisateur.

---

## 5. Points clés

- Le système est asynchrone : upload + génération ne bloquent pas l'utilisateur.
- `process_course` est la porte d’entrée pour transformer un PDF en contenu indexé.
- Les générations de quiz/flashcards démarrent par un enregistrement immédiat en base, puis sont traitées par Celery.
- Les files d’attente `courses` et `generation` permettent de dissocier le pipeline de traitement de fichiers du pipeline de génération de contenu pédagogique.
- Les throttles empêchent la surcharge et limitent les usages abusifs par utilisateur.
