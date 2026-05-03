from decouple import config

# ─── Fichiers de cours ───────────────────────────────────────
COURSE_ALLOWED_EXTENSIONS = config(
    'COURSE_ALLOWED_EXTENSIONS',
    default='pdf,png,jpg,jpeg,webp'
).split(',')
COURSE_MAX_FILE_SIZE_MB = config('COURSE_MAX_FILE_SIZE_MB', default=20, cast=int)
COURSE_CHUNK_SIZE = config('COURSE_CHUNK_SIZE', default=500, cast=int)
COURSE_CHUNK_OVERLAP = config('COURSE_CHUNK_OVERLAP', default=50, cast=int)
COURSE_SEARCH_RESULTS = config('COURSE_SEARCH_RESULTS', default=8, cast=int)

# ─── Flashcards ────────────────────────────────────────────
FLASHCARDS_MIN_CARDS = config('FLASHCARDS_MIN_CARDS', default=3, cast=int)
FLASHCARDS_MAX_CARDS = config('FLASHCARDS_MAX_CARDS', default=300, cast=int)
FLASHCARDS_DEFAULT_CARDS = config('FLASHCARDS_DEFAULT_CARDS', default=10, cast=int)
FLASHCARDS_RESULTS = config('FLASHCARDS_RESULTS', default=8, cast=int)

# ─── Quiz ──────────────────────────────────────────────────
QUIZ_MIN_QUESTIONS = config('QUIZ_MIN_QUESTIONS', default=3, cast=int)
QUIZ_MAX_QUESTIONS = config('QUIZ_MAX_QUESTIONS', default=200, cast=int)
QUIZ_DEFAULT_QUESTIONS = config('QUIZ_DEFAULT_QUESTIONS', default=5, cast=int)
QUIZ_SEARCH_RESULTS = config('QUIZ_SEARCH_RESULTS', default=6, cast=int)

# ─── Throttle DRF ──────────────────────────────────────────
COURSE_UPLOAD_RATE = config('COURSE_UPLOAD_RATE', default='5/hour')
GENERATION_RATE = config('GENERATION_RATE', default='10/day')
