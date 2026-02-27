from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False, unique=True)
    file_type = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))
    
    # Additional fields from the migration
    content = db.Column(db.Text)
    content_vector = db.Column(TSVECTOR)
    embeddings = db.Column(JSONB)
    
    # Create indexes (matching the migration)
    __table_args__ = (
        db.Index('idx_documents_user_id', 'user_id'),
        db.Index('idx_documents_status', 'status'),
    )
    
    def __repr__(self):
        return f'<Document {self.filename}>' 