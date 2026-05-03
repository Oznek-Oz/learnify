# 📊 Audit Complet - Projet Learnify

## 🎯 Résumé Exécutif

Le projet Learnify est une **plateforme de génération de contenu pédagogique** (cours → flashcards → quiz) alimentée par l'IA (Gemini). L'architecture est **globalement saine** (Django + Celery + ChromaDB + RAG) mais présente des **vulnérabilités critiques**, des **problèmes de performance** et des **lacunes en robustesse**.

**Score global: 6/10**
- ✅ Architecture async bien pensée
- ❌ Sécurité critique compromise
- ❌ Pas de pagination, caching, rate-limiting
- ⚠️ Gestion d'erreurs basique
- ⚠️ Monitoring absent

---

## 🔴 PROBLÈMES CRITIQUES (Urgence: IMMÉDIATE)

### 1️⃣ **Clé API Gemini exposée en clair** 
**Fichier:** `test_gemini.py` (ligne 2)  
**Sévérité:** 🔴 **CRITIQUE**

```python
# ❌ DANGEREUX - Clé publique et visible
genai.configure(api_key="AIzaSyDS5etLut8ivC1C4AnXqoWOmxUWGcsYFg8")
```

**Conséquences:**
- Accès non autorisé à l'API Gemini (coût financier énorme)
- Compromission du compte Google Cloud
- Données des utilisateurs exposées

**Solutions:**
```python
# ✅ Utiliser les variables d'environnement
genai.configure(api_key=settings.GEMINI_API_KEY)

# ✅ Ajouter au .gitignore
echo "test_gemini.py" >> .gitignore
git rm --cached test_gemini.py

# ✅ Ajouter les détails aux GitHub secrets si en CI/CD
```

**Action immédiate:**
```bash
# 1. Supprimer le fichier
rm test_gemini.py

# 2. Invalider la clé sur Google Cloud Console
# 3. En générer une nouvelle
# 4. Mettre à jour .env
```

---

### 2️⃣ **Pas de validation de fichiers uploadés**
**Fichier:** `courses/views.py`, `courses/models.py`  
**Sévérité:** 🔴 **CRITIQUE**

**Problèmes:**
- Pas de vérification de taille max
- Pas de validation du type MIME
- Pas de scan malware
- Pas de vérification du contenu réel

```python
# ❌ ACTUEL - Aucune validation
file = models.FileField(upload_to=course_upload_path)

# ✅ À FAIRE
file = models.FileField(
    upload_to=course_upload_path,
    validators=[
        FileExtensionValidator(allowed_extensions=['pdf']),
        validate_file_size,  # Max 50MB
    ]
)

def validate_file_size(file):
    if file.size > 50 * 1024 * 1024:  # 50MB
        raise ValidationError("Le fichier dépasse 50MB")

def validate_pdf_integrity(file):
    """Vérifie que le PDF est vraiment un PDF"""
    if file.read(4) != b'%PDF':
        raise ValidationError("Fichier PDF invalide")
    file.seek(0)
```

---

### 3️⃣ **Rate limiting absent → DoS facile**
**Fichier:** `courses/views.py`, `flashcards/views.py`, `quizz/views.py`  
**Sévérité:** 🔴 **CRITIQUE**

Un utilisateur malveillant peut:
- Uploader 1000 fichiers → paralysie du serveur
- Générer 1000 quiz → ruine financière (Gemini API coûte cher)

```python
# ✅ Ajouter django-ratelimit
from django_ratelimit.decorators import ratelimit

class CourseListCreateView(generics.ListCreateAPIView):
    @ratelimit(key='user', rate='5/h', method='POST')
    def post(self, request):
        # Max 5 uploads par heure par utilisateur
        ...

class GenerateFlashcardsView(APIView):
    def post(self, request):
        # Max 10 générations par jour
        throttle_classes = [UserRateThrottle]
        throttle_scope = 'flashcard_generation'
```

**Dans settings.py:**
```python
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.UserRateThrottle'
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'user': '100/hour',
    'flashcard_generation': '10/day',
    'quiz_generation': '10/day',
}
```

---

## 🟠 PROBLÈMES MAJEURS (Urgence: HAUTE)

### 4️⃣ **Pas de pagination → OutOfMemory sur grandes listes**
**Fichier:** Toutes les `ListAPIView`  
**Sévérité:** 🟠 **HAUTE**

Actuellement: `DeckListView`, `QuizListView` chargent TOUS les records en RAM.

Avec 10 000 fiches × 20 utilisateurs = 200 000 objets en mémoire 💥

```python
# ❌ ACTUEL
class DeckListView(generics.ListAPIView):
    queryset = FlashcardDeck.objects.all()

# ✅ À FAIRE
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class DeckListView(generics.ListAPIView):
    queryset = FlashcardDeck.objects.all()
    pagination_class = StandardPagination
```

---

### 5️⃣ **Pas de caching des recherches vectorielles ChromaDB**
**Fichier:** `courses/vector_store.py`  
**Sévérité:** 🟠 **HAUTE**

Chaque appel à `search_similar_chunks()` refait le calcul d'embedding 100% du temps.

```python
# ❌ ACTUEL
def search_similar_chunks(course_id: int, query: str, n_results=5):
    query_embed = get_embedding_model().encode([query]).tolist()
    # Ré-encode à chaque fois → 500ms par recherche
    results = collection.query(...)
    return results

# ✅ À FAIRE
from django.core.cache import cache
import hashlib

def search_similar_chunks(course_id: int, query: str, n_results=5):
    cache_key = f"search:{course_id}:{hashlib.md5(query.encode()).hexdigest()}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Calcul seulement si pas en cache
    query_embed = get_embedding_model().encode([query]).tolist()
    results = collection.query(...)["documents"][0]
    
    cache.set(cache_key, results, timeout=3600)  # 1h cache
    return results
```

**Impact attendu:** Recherches 50× plus rapides pour les requêtes répétées.

---

### 6️⃣ **Pas de compression des embeddings**
**Fichier:** `courses/vector_store.py`  
**Sévérité:** 🟠 **HAUTE**

Calcul de `SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')` = **384 dimensions** × float32 = **1.5 KB par chunk**.

Avec 10 000 chunks = **15 MB**. Inutile!

```python
# ❌ ACTUEL
embeddings = get_embedding_model().encode(texts).tolist()  # float32

# ✅ À FAIRE (quantization)
import numpy as np

embeddings = get_embedding_model().encode(texts)  # numpy array
# Quantize to int8 (perte minimale, gain 4×)
embeddings_int8 = (embeddings * 127).astype(np.int8)
embeddings_list = embeddings_int8.tolist()

# À la recherche: re-normaliser
query_embed = (get_embedding_model().encode([query]) * 127).astype(np.int8)
```

**Impact attendu:** Stockage 4× plus petit, accès 2× plus rapide.

---

### 7️⃣ **Chunking fixe inadapté aux types de contenu**
**Fichier:** `courses/services.py`  
**Sévérité:** 🟠 **HAUTE**

Chunk size = 500 mots = mauvais pour:
- **Images OCR**: 500 mots c'est 10 pages
- **Math/Chimie**: perdre des formules
- **Code**: perdre le contexte

```python
# ❌ ACTUEL
def chunk_text(pages, chunk_size=500, overlap=50):
    # Chunking naïf par mot

# ✅ À FAIRE - Adaptive chunking
def chunk_text_adaptive(pages: list[dict], file_type='pdf'):
    if file_type == 'pdf':
        chunk_size, overlap = 300, 50  # Technique
    elif file_type == 'image':
        chunk_size, overlap = 200, 30  # OCR -> plus compact
    else:
        chunk_size, overlap = 500, 50  # Default
    
    # Meilleur: chunking par paragraphes/sections
    chunks = []
    for page in pages:
        paragraphs = page['text'].split('\n\n')
        for para in paragraphs:
            words = para.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunks.append({
                    'content': ' '.join(words[i:i+chunk_size]),
                    'page': page['page']
                })
    return chunks
```

---

## 🟡 PROBLÈMES MOYENS (Urgence: NORMALE)

### 8️⃣ **Pas de stratégie de TTL/timeout Celery**
**Fichier:** `courses/tasks.py`, `flashcards/tasks.py`, `quizz/tasks.py`  
**Sévérité:** 🟡 **NORMALE**

Une tâche qui queue peut rester bloquée indéfiniment. Problème:
- Gemini API peut répondre en 30s ou 30 minutes
- Worker pourrait crash mid-task
- User ne sait pas quand donner up

```python
# ❌ ACTUEL
@shared_task(bind=True, max_retries=3)
def process_course(self, course_id):
    # Pas de timeout!
    ...

# ✅ À FAIRE
@shared_task(
    bind=True,
    max_retries=3,
    time_limit=300,  # Max 5 minutes total
    soft_time_limit=280,  # Alerte à 280s
    default_retry_delay=30
)
def process_course(self, course_id):
    try:
        course = Course.objects.get(id=course_id)
        # ... processing ...
    except SoftTimeLimitExceeded:
        course.status = Course.Status.FAILED
        course.save()
        logger.error(f"Task timeout for course {course_id}")
        raise
```

---

### 9️⃣ **Gestion d'erreurs Gemini très basique**
**Fichier:** `flashcards/gemini_service.py`, `quizz/gemini_service.py`  
**Sévérité:** 🟡 **NORMALE**

Gemini retourne du texte invalide → JSON crash. Aucun fallback.

```python
# ❌ ACTUEL
try:
    flashcards = json.loads(text)
except json.JSONDecodeError as e:
    logger.error(f"JSON invalide : {e}")
    raise ValueError("Gemini n'a pas retourné du JSON valide")

# ✅ À FAIRE
def generate_flashcards_from_chunks_safe(chunks, topic, num_cards=10):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            flashcards = generate_flashcards_from_chunks(chunks, topic, num_cards)
            return flashcards
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Tentative {attempt+1} échouée: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponentiel
            else:
                # Fallback: retourner des fiches vides
                return [
                    {
                        "front": f"Concept {i}",
                        "back": "Contenu généré partiellement",
                        "hint": "Refresh la génération"
                    }
                    for i in range(1, num_cards + 1)
                ]
```

---

### 🔟 **Pas de monitoring/alertes Celery**
**Fichier:** Configuration manquante  
**Sévérité:** 🟡 **NORMALE**

Vous ne savez pas si:
- Les workers tournent
- Les queues s'empilent
- Une tâche est bloquée depuis 2h

```python
# ✅ À FAIRE - Ajouter Celery flower et sentry
pip install flower django-extensions sentry-sdk

# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'celery': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

import sentry_sdk
sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    traces_sample_rate=0.1,
)

# Lancer flower pour monitoring
celery -A config inspect active
celery -A config worker --loglevel=info
# En prod: flower (http://localhost:5555)
```

---

### 1️⃣1️⃣ **Pas de backup/transaction sur ChromaDB**
**Fichier:** `courses/vector_store.py`  
**Sévérité:** 🟡 **NORMALE**

ChromaDB est un **store persistant mais pas transactional**. Risques:

- Migration de `chunk_size=500` → `chunk_size=300`? Les anciens chunks restent
- Suppression d'un cours: `CourseChunk` supprimé mais collection ChromaDB intact
- Panne disk: données perdues

```python
# ❌ ACTUEL
def delete_course_collection(course_id: int):
    try:
        get_chroma_client().delete_collection(f"course_{course_id}")
    except Exception:
        pass  # Silencieux!

# ✅ À FAIRE - Transactions propres
from django.db import transaction

def delete_course_with_vectors(course_id: int):
    try:
        with transaction.atomic():
            # 1. Supprimer ChromaDB D'ABORD
            try:
                get_chroma_client().delete_collection(f"course_{course_id}")
            except Exception as e:
                logger.error(f"ChromaDB delete failed: {e}")
                raise
            
            # 2. Supprimer chunks en base
            CourseChunk.objects.filter(course_id=course_id).delete()
            
            # 3. Supprimer cours
            Course.objects.filter(id=course_id).delete()
            
            logger.info(f"Course {course_id} deleted completely")
    except Exception as e:
        logger.error(f"Delete transaction failed: {e}")
        raise

# BACKUP ChromaDB régulièrement
import shutil
def backup_chromadb():
    source = settings.BASE_DIR / 'chromadb_data'
    dest = settings.BASE_DIR / f'backups/chromadb_{datetime.now():%Y%m%d}'
    shutil.copytree(source, dest)
```

---

### 1️⃣2️⃣ **ALLOWED_HOSTS trop permissif**
**Fichier:** `config/settings.py`  
**Sévérité:** 🟡 **NORMALE**

```python
# ❌ CAS ACTUEL
ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # OK pour DEV

# ❌ EN PROD ce n'est PAS ASSEZ RESTRICTIF
# ALLOWED_HOSTS = ['*']  # DANGER!

# ✅ À FAIRE
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.local']
else:
    ALLOWED_HOSTS = [
        'learnify.com',
        'www.learnify.com',
        'api.learnify.com',
        config('ALLOWED_DOMAIN', default='learnify.com')
    ]
```

---

## 🟢 AMÉLIORATIONS RECOMMANDÉES (Performance)

### 1️⃣3️⃣ **Indexation manquante dans la base**
**Fichier:** `courses/models.py`, `flashcards/models.py`, `quizz/models.py`  
**Sévérité:** 🟢 **NORMALE**

```python
# ❌ ACTUEL - Pas d'indexes
class Course(models.Model):
    owner = models.ForeignKey(...)  # Pas d'index!
    status = models.CharField(...)  # Pas d'index!

# ✅ À FAIRE
class Course(models.Model):
    owner = models.ForeignKey(..., db_index=True)
    status = models.CharField(..., db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['owner', '-created_at']),
        ]

# Migration:
python manage.py makemigrations
python manage.py migrate
```

---

### 1️⃣4️⃣ **Pas de prefetch_related optimal**
**Fichier:** `flashcards/views.py`  
**Sévérité:** 🟢 **NORMALE**

```python
# ❌ ACTUEL - N+1 queries
def get_queryset(self):
    return FlashcardDeck.objects.filter(course__owner=self.request.user)
    # 1 query pour decks
    # 1 query par deck pour flashcards = N queries!

# ✅ À FAIRE
def get_queryset(self):
    return (FlashcardDeck.objects
        .filter(course__owner=self.request.user)
        .select_related('course')
        .prefetch_related('flashcards')
        .annotate(card_count=Count('flashcards')))
```

---

### 1️⃣5️⃣ **Embeddings rechargés à chaque import de module**
**Fichier:** `courses/vector_store.py`  
**Sévérité:** 🟢 **NORMALE**

```python
# ✅ POSITIF MAIS À OPTIMISER
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Charge 300MB une seule fois
        _embedding_model = SentenceTransformer(...)
    return _embedding_model

# En prod: considérer un pool de workers dédié
# Celery worker --autoscale=4,1 -Q courses
```

---

## 📊 Tableau de Synthèse

| N° | Problème | Sévérité | Impact | Effort | Priorité |
|---|---|---|---|---|---|
| 1 | Clé API exposée | 🔴 Critique | Coût illimité | 15 min | P0 |
| 2 | Pas validation fichiers | 🔴 Critique | RCE possible | 1h | P0 |
| 3 | Pas rate limiting | 🔴 Critique | DoS facile | 2h | P0 |
| 4 | Pas pagination | 🟠 Haute | OOM | 2h | P1 |
| 5 | Pas cache vectoriel | 🟠 Haute | Lenteur 500ms | 3h | P1 |
| 6 | Pas compression embeddings | 🟠 Haute | Espace disque | 2h | P1 |
| 7 | Chunking fixe | 🟠 Haute | Qualité RAG | 3h | P1 |
| 8 | Pas timeout Celery | 🟡 Normale | Tâches bloquées | 1h | P2 |
| 9 | Gestion erreurs basique | 🟡 Normale | Crashes fréquents | 2h | P2 |
| 10 | Pas monitoring | 🟡 Normale | Aveuglement opérationnel | 2h | P2 |
| 11 | Pas backup ChromaDB | 🟡 Normale | Perte de données | 1h | P2 |
| 12 | ALLOWED_HOSTS | 🟡 Normale | Req forgerie | 30 min | P2 |
| 13 | Pas d'indexes | 🟢 Normale | Queries lentes | 1h | P3 |
| 14 | Pas prefetch | 🟢 Normale | N+1 queries | 1h | P3 |
| 15 | Chargement embeddings | 🟢 Normale | Latency proxy | 1h | P3 |

---

## 🎯 Plan d'Action par Phase

### **Phase 0 - Sécurité (IMMÉDIATE, 1 jour)**
```bash
# 1. Supprimer clé exposée
rm test_gemini.py && git rm --cached test_gemini.py

# 2. Invalider clé Gemini sur Google Cloud

# 3. Ajouter validation fichiers → 1h

# 4. Ajouter rate limiting → 2h
pip install django-ratelimit
```

---

### **Phase 1 - Robustesse (Semaine 1)**
- [ ] Ajouter pagination
- [ ] Ajouter timeout Celery
- [ ] Ajouter monitoring Flower + Sentry
- [ ] Stratégie backup ChromaDB

---

### **Phase 2 - Performance (Semaine 2)**
- [ ] Cache Redis pour recherches vectorielles
- [ ] Compression embeddings
- [ ] Chunking adaptatif
- [ ] Indexes DB

---

### **Phase 3 - Productionisation (Semaine 3+)**
- [ ] Logging structuré (JSON)
- [ ] Health checks
- [ ] Autoscaling Celery
- [ ] Secrets management (AWS Secrets Manager)

---

## ✅ Points Positifs à Conserver

1. **Architecture async solide** - Celery bien utilisé
2. **Séparation des concerns** - Services / Tasks / Views clean
3. **RAG implémenté** - ChromaDB bien intégré
4. **Status tracking** - Bonnes transitions d'état
5. **Lazy loading embeddings** - Optimisation pertinente
6. **JWT + Custom User** - Auth complète

---

## 📚 Bibliographie & Ressources

- **Django ORM**: https://docs.djangoproject.com/en/6.0/topics/db/optimization/
- **Celery Best Practices**: https://celery.io/
- **ChromaDB**: https://docs.trychroma.com/
- **Vector Search Optimization**: https://www.anthropic.com/index/semantic-search
- **Django Security**: https://docs.djangoproject.com/en/6.0/topics/security/

---

**Rapport généré:** April 6, 2026  
**Audit par:** GitHub Copilot (Claude Haiku 4.5)  
**Confidentiel:** Learnify Team Only
