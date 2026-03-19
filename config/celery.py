# config/celery.py

import os
from celery import Celery

# Dit à Celery où trouver les settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('learnify')

# Charge la config Celery depuis settings.py (préfixe CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvre automatiquement les tasks.py dans chaque app Django
app.autodiscover_tasks()