"""
Celery Application Configuration
"""
from celery import Celery
import os

# Get Redis URL from environment (fallback to localhost for development)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    'healthscan',
    broker=redis_url,
    backend=redis_url,
    include=['workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time (important for browser automation)
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks (prevent memory leaks)
)

