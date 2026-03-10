from flask import Flask, jsonify
from flask_cors import CORS
import os
from extensions import db, login_manager, migrate
from blueprints.auth.models import User
import logging
from sqlalchemy.exc import OperationalError
import time
import psutil
import sys

def get_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'memory_percent': process.memory_percent(),
        'rss': memory_info.rss / 1024 / 1024,  # RSS in MB
        'vms': memory_info.vms / 1024 / 1024,  # VMS in MB
    }

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')
    
    # Use DATABASE_URL directly from environment
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    
    # Add ML API URL configuration
    app.config['ML_API_URL'] = os.getenv('ML_API_URL', 'http://localhost:8000')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    logging.info(app.config)
    # Initialize extensions with app
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Import and register blueprints
    from blueprints.auth import auth_bp
    from blueprints.documents import documents_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    
    @app.route('/memory')
    def memory_usage():
        return jsonify({
            'app_memory': get_memory_usage(),
            'workers': 'Use ps command to see worker memory',
            'python_version': sys.version,
        })
    
    # Create all database tables with retry logic
    with app.app_context():
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                db.create_all()
                logging.info("Successfully connected to database and created tables")
                break
            except OperationalError as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to connect to database after {max_retries} attempts")
                    raise
                logging.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True) 