import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_core.settings')

app = Celery('chess_core')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    imports=(
        'game.task', 
    )
)

app.autodiscover_tasks()