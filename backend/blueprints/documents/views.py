from flask import render_template, redirect, url_for, request, current_app, flash, abort, jsonify
from flask_login import login_required, current_user
from . import documents_bp
from .models import Document
from extensions import db
import os
from sqlalchemy import or_, func
from workers.celery_app import celery_app
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import logging
import requests

logger = logging.getLogger(__name__)

@documents_bp.route('/')
@login_required
def index():
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.created_at.desc()).all()
    return render_template('documents/index.html', documents=documents)

@documents_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file:
            filename = file.filename
            file_type = file.content_type
            
            # Read file content based on type
            content = None
            try:
                if file_type == 'application/pdf':
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = ''
                    for page in pdf_reader.pages:
                        content += page.extract_text()
                    logger.info(f"Extracted PDF content length: {len(content)}")
                    logger.info(f"First 10 chars of PDF content: {content[:10]}")
                elif file_type == 'text/plain':
                    content = file.read().decode('utf-8')
                    logger.info(f"Extracted text content length: {len(content)}")
                    logger.info(f"First 10 chars of text content: {content[:10]}")
                else:
                    flash('Unsupported file type')
                    return redirect(request.url)
                
                if not content or len(content.strip()) == 0:
                    # this may happen to some pdfs, need to debug and fix
                    logger.error("Extracted content is empty")
                    flash('Could not extract content from file')
                    return redirect(request.url)
                
                # Get file size from content
                size = len(content.encode('utf-8'))
                
                document = Document(
                    user_id=current_user.id,
                    filename=filename,
                    file_path=filename,
                    file_type=file_type,
                    size=size,
                    status='pending',
                    content=content
                )
                
                db.session.add(document)
                db.session.commit()
                logger.info(f"Saved document {document.id} to database with content length: {len(document.content)}")
                
                # Use the celery app to trigger document processing
                celery_app.send_task('workers.document_processor.process_document', args=[document.id])
                
                flash('Document uploaded successfully')
                return redirect(url_for('documents.index'))
                
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
        
    return render_template('documents/create.html')

@documents_bp.route('/delete/<int:document_id>', methods=['POST'])
@login_required
def delete(document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first_or_404()
    
    # Delete the physical file
    try:
        os.remove(document.file_path)
    except OSError:
        pass  # File might not exist
    
    # Delete from database
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully')
    return redirect(url_for('documents.index'))

@documents_bp.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    if query:
        # Search in filename and content using PostgreSQL full-text search
        documents = Document.query.filter(
            Document.user_id == current_user.id,
            or_(
                Document.filename.ilike(f'%{query}%'),
                Document.content_vector.match(query)
            )
        ).order_by(Document.created_at.desc()).all()
    else:
        documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.created_at.desc()).all()
    
    return render_template('documents/index.html', documents=documents)

@documents_bp.route('/view/<int:document_id>')
@login_required
def view(document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first_or_404()
    return render_template('documents/view.html', document=document)

@documents_bp.route('/search_suggestions')
@login_required
def search_suggestions():
    query = request.args.get('query', '')
    if not query or len(query) < 2:
        return jsonify({'results': []})

    # First, get documents by text match
    documents = Document.query.filter(Document.user_id == current_user.id).all()

    # Get query embedding from ML API
    model_api_url = os.getenv('MODEL_API_URL', 'http://localhost:8000')
    try:
        response = requests.post(
            f"{model_api_url}/api/v1/embeddings",
            json={"texts": [query]},
            timeout=30
        )
        logger.info(f"ML API Response status: {response.status_code}")
        response.raise_for_status()
        query_embedding = np.array(response.json()["embeddings"][0]).reshape(1, -1)
    except Exception as e:
        logger.error(f"Error getting embeddings from model API: {str(e)}")
        return jsonify({'results': [], 'error': 'Error calculating similarities'})

    results = []
    for doc in documents:
        # Calculate similarity score if embeddings exist
        similarity_score = 0
        if doc.embeddings:
            doc_embedding = np.array(doc.embeddings).reshape(1, -1)
            similarity_score = float(cosine_similarity(query_embedding, doc_embedding)[0][0])

        # Get content preview with highlighted search term
        preview = ''
        if doc.content:
            query_lower = query.lower()
            content_lower = doc.content.lower()
            pos = content_lower.find(query_lower)
            if pos >= 0:
                start = max(0, pos - 50)
                end = min(len(doc.content), pos + len(query) + 50)
                preview = doc.content[start:end]
                if start > 0:
                    preview = '...' + preview
                if end < len(doc.content):
                    preview = preview + '...'
                preview = re.sub(
                    f'({query})',
                    r'<span class="highlight">\1</span>',
                    preview,
                    flags=re.IGNORECASE
                )

        results.append({
            'filename': doc.filename,
            'preview': preview or 'No preview available',
            'url': url_for('documents.view', document_id=doc.id),
            'similarity': similarity_score
        })

    # Sort by similarity score and take top 5
    results.sort(key=lambda x: x['similarity'], reverse=True)
    results = results[:5]

    return jsonify({'results': results}) 