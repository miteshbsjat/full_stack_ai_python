from celery import Celery
from flask import Flask
from extensions import db
from config.celery import CELERY_TASK_LIST, CELERY_CONFIG
import os

def create_app():
    """Create Flask application."""
    app = Flask(__name__)
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Add Celery config
    app.config.update(CELERY_CONFIG)
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def create_celery_app(app=None):
    """
    Create a new Celery object and tie together the Celery config to the app's
    config. Wrap all tasks in the context of the application.
    """
    app = app or create_app()

    celery = Celery(app.import_name,
                    broker=app.config['broker_url'],
                    include=CELERY_TASK_LIST)

    # Update Celery config with Flask app config
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(ContextTask, self).__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create the Flask app and Celery instances
flask_app = create_app()
celery_app = create_celery_app(flask_app) 