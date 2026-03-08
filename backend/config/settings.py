import os
from pathlib import Path

# Flask settings
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Server settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL')

# Set the SQLAlchemy URI from DATABASE_URL
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis settings
REDIS_URL = os.getenv('REDIS_URL')

# File upload settings
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

# CORS settings
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
CORS_ORIGINS = [FRONTEND_URL]
CORS_SUPPORTS_CREDENTIALS = True  # Allow credentials (cookies, authorization headers)

# Session settings
SESSION_TYPE = 'redis'
SESSION_REDIS = REDIS_URL
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

# Search settings
BASE_MODEL_DIR = os.getenv('BASE_MODEL_DIR', os.path.join(BASE_DIR, 'ml_models'))
SEARCH_MODEL_PATH = os.path.join(BASE_MODEL_DIR, 'sentence_transformer_model')
SEARCH_MODEL_NAME = os.getenv('SEARCH_MODEL_NAME', 'all-MiniLM-L6-v2')  
MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.3))

# Security settings
PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
PASSWORD_MAX_LENGTH = int(os.getenv('PASSWORD_MAX_LENGTH', 72))  # Bcrypt maximum

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Development-specific settings
if FLASK_ENV == 'development':
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries

# Production-specific settings
elif FLASK_ENV == 'production':
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # Add any production-specific settings here

# Testing-specific settings
elif FLASK_ENV == 'testing':
    DEBUG = True
    TESTING = True
    # Use test database URL if provided, otherwise modify the main DATABASE_URL for testing
    TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')
    if TEST_DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URL
    # elif DATABASE_URL:
        # Modify the main DATABASE_URL to use a test database
        # SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace(DB_NAME, f"{DB_NAME}_test")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'test_uploads') 