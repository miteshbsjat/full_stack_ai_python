#!/bin/bash

# Run migrations
flask db upgrade

# Print initial memory usage
echo "Initial memory usage:"
ps -o pid,ppid,%mem,rss,command -p $$

# Start the application with Gunicorn and monitor
gunicorn --bind 0.0.0.0:5002 \
         --workers 2 \
         --threads 2 \
         --worker-class gthread \
         --worker-tmp-dir /dev/shm \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --log-level info \
         --access-logfile - \
         --error-logfile - \
         "app:create_app()"

# The memory usage of Gunicorn workers can be seen with:
# ps -o pid,ppid,%mem,rss,command ax | grep gunicorn