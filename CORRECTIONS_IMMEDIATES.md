# 🔧 Plan d'Action - Corrections Immédiates

## ⚠️ CRITIQUES (À faire DÈS MAINTENANT)

### 1. Supprimer la clé API exposée

```bash
# Terminal
rm test_gemini.py
git rm --cached test_gemini.py  # Si déjà commit
echo "test_gemini.py" >> .gitignore
git add .gitignore
git commit -m "security: remove exposed Gemini API key"

# URGENT: Invalider la clé sur Google Cloud Console
# https://console.cloud.google.com -> APIs & Services -> Credentials
# Puis regénérer une nouvelle clé
```

**Vérifier que c'est bien fait:**
```bash
grep -r "AIzaSy" .  # Doit retourner RIEN (sauf dans .gitignore)
```

---

### 2. Ajouter validation de fichiers

**Créer:** `courses/validators.py`

```python
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

def validate_pdf_file(file: UploadedFile):
    """Vérifie que c'est vraiment un PDF valide"""
    # Vérifier l'extension
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError("Le fichier doit être en PDF")
    
    # Vérifier la taille
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"Le fichier ne doit pas dépasser {MAX_FILE_SIZE/1024/1024:.0f} MB")
    
    # Vérifier la signature PDF (magic bytes)
    file.seek(0)
    header = file.read(4)
    file.seek(0)
    
    if header != b'%PDF':
        raise ValidationError("Fichier PDF invalide (signature incorrecte)")

def validate_image_file(file: UploadedFile):
    """Vérifie que c'est vraiment une image"""
    allowed_mimes = ['image/jpeg', 'image/png', 'image/webp']
    
    if file.content_type not in allowed_mimes:
        raise ValidationError(f"Format image non supporté. Utilisez JPEG, PNG ou WebP")
    
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"L'image ne doit pas dépasser {MAX_FILE_SIZE/1024/1024:.0f} MB")
```

**Modifier:** `courses/models.py`

```python
from django.core.validators import FileExtensionValidator
from .validators import validate_pdf_file

class Course(models.Model):
    # ... existing code ...
    file = models.FileField(
        upload_to=course_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_pdf_file,  # ← NOUVEAU
        ]
    )
```

**Modifier:** `courses/views.py`

```python
class CourseListCreateView(generics.ListCreateAPIView):
    def create(self, request, *args, **kwargs):
        # Valider le fichier explicitement
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Déclenche les validators
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
```

---

### 3. Ajouter Rate Limiting

**Installer:**
```bash
pip install djangorestframework
```

**Modifier:** `config/settings.py`

```python
REST_FRAMEWORK = {
    # ... existing config ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',  # Global
        'course_upload': '5/hour',
        'generation': '10/day',
    }
}
```

**Créer:** `courses/throttles.py`

```python
from rest_framework.throttling import UserRateThrottle

class CourseUploadThrottle(UserRateThrottle):
    scope = 'course_upload'  # Max 5/hour

class GenerationThrottle(UserRateThrottle):
    scope = 'generation'  # Max 10/day
```

**Modifier:** `courses/views.py`

```python
from .throttles import CourseUploadThrottle

class CourseListCreateView(generics.ListCreateAPIView):
    throttle_classes = [CourseUploadThrottle]
    # ... rest of code
```

**Modifier:** `flashcards/views.py` et `quizz/views.py`

```python
from courses.throttles import GenerationThrottle

class GenerateFlashcardsView(APIView):
    throttle_classes = [GenerationThrottle]
    # ...

class GenerateQuizView(APIView):
    throttle_classes = [GenerationThrottle]
    # ...
```

---

## 📋 Tester les changements

```bash
# 1. Tester validation fichier
python manage.py shell
from courses.models import Course
from django.core.files.uploadedfile import SimpleUploadedFile

# Créer un faux PDF
bad_file = SimpleUploadedFile("test.pdf", b"Not a PDF")
course = Course(file=bad_file, owner=request.user)
course.full_clean()  # Doit lever ValidationError ✓

# 2. Tester rate limiting
# Faire 6 requêtes POST en moins de 1 heure
# La 6e doit retourner 429 Too Many Requests ✓

# 3. Vérifier les clés API
grep -r "AIzaSy" . --exclude-dir=venv --exclude-dir=.git
# Doit retourner RIEN ✓
```

---

## ✅ Checklist Urgente

- [ ] Supprimer `test_gemini.py` et invalider clé Gemini
- [ ] Ajouter `courses/validators.py`
- [ ] Modifier `courses/models.py` avec validators
- [ ] Modifier `courses/views.py` avec validation
- [ ] Ajouter rate limiting dans `settings.py`
- [ ] Ajouter `courses/throttles.py`
- [ ] Modifier flashcards/quizz views avec throttles
- [ ] Tester localement
- [ ] Commit & Push
- [ ] Monitorer les logs en prod

---

## 📈 Prochaines Étapes (Phase 1)

Après les corrections critiques, faire:

1. **Pagination** → 2h
2. **Celery Timeouts** → 1h
3. **Monitoring (Flower)** → 2h
4. **Cache vectoriel** → 3h

Voir `AUDIT_RAPPORT.md` pour le détail complet.
