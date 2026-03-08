import os

CELERY_TASK_LIST = [
    'workers.document_processor',
]

CELERY_CONFIG = {
    'broker_url': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    'result_backend': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    # Memory optimization settings
    'worker_max_memory_per_child': 150000,  # Restart worker after using 150MB
    'worker_max_tasks_per_child': 50,       # Restart worker after 50 tasks
    'worker_prefetch_multiplier': 1,        # Don't prefetch tasks
    'task_time_limit': 1800,                # 30 minute timeout
    'task_soft_time_limit': 1500,           # Soft timeout 25 minutes
} 