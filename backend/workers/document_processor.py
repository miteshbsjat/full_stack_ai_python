from .celery_app import celery_app
from blueprints.documents.models import Document
from extensions import db
import os
from sqlalchemy import func
import logging
import gc
import psutil
import sys
import requests
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_process_memory():
    """Get the memory usage of the current process in MB"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / 1024 / 1024  # Convert to MB

def get_embeddings(text: str) -> list:
    """Get embeddings from the model API."""
    model_api_url = os.getenv('MODEL_API_URL', 'http://localhost:8000')  # Default to localhost if not set
    try:
        response = requests.post(
            f"{model_api_url}/api/v1/embeddings",
            json={"texts": [text]},
            timeout=30
        )
        if response.status_code == 503:
            logger.error("Model API service unavailable")
            raise Exception("Model service temporarily unavailable")
        response.raise_for_status()
        return response.json()["embeddings"][0]
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to Model API at {model_api_url}")
        raise Exception("Model service connection failed")
    except requests.exceptions.Timeout:
        logger.error("Model API request timed out")
        raise Exception("Model service request timed out")
    except Exception as e:
        logger.error(f"Error getting embeddings from model API: {str(e)}")
        raise

@celery_app.task(bind=True)
def process_document(self, document_id):
    """Process uploaded document and generate embeddings."""
    initial_memory = get_process_memory()
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    logger.info(f"Processing document {document_id}")
    
    try:
        document = Document.query.get(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return {'error': f'Document {document_id} not found'}

        if not document.content:
            document.status = 'error'
            document.error_message = 'Document has no content'
            db.session.commit()
            logger.error(f"Document {document_id} has no content")
            return {'error': f'Document has no content'}

        logger.info(f"Processing document content of length: {len(document.content)}")
        
        # Get embeddings from model API
        try:
            embeddings = get_embeddings(document.content)
            logger.info("Successfully generated embeddings from model API")
            logger.info(type(embeddings))
            # logger.info(embeddings)
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            document.status = 'error'
            document.error_message = f'Error generating embeddings: {str(e)}'
            db.session.commit()
            return {'error': str(e)}
        
        # Store embeddings as JSON
        document.embeddings = embeddings
        
        # Create text search vector
        document.content_vector = func.to_tsvector('english', document.content)
        
        # Update status
        document.status = 'processed'
        db.session.commit()
        logger.info(f"Memory before cleanup: {get_process_memory():.2f} MB")
        
        # Clear some memory
        gc.collect()
        logger.info(f"Final memory usage: {get_process_memory():.2f} MB")
        
        logger.info(f"Successfully processed document {document_id}")
        return {'status': 'success', 'document_id': document_id}
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        if 'document' in locals():
            document.status = 'error'
            document.error_message = str(e)
            db.session.commit()
        return {'error': f'Error processing document {document_id}: {str(e)}'}

# Configure Celery to use Flask app context
class FlaskTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        from app import create_app
        with create_app().app_context():
            return self.run(*args, **kwargs)

celery_app.Task = FlaskTask 