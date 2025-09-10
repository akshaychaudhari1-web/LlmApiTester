from app import db
from datetime import datetime
import json

class Document(db.Model):
    """Model for storing uploaded PDF documents"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    page_count = db.Column(db.Integer)
    
    # Chunks relationship
    chunks = db.relationship('DocumentChunk', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat(),
            'processed': self.processed,
            'page_count': self.page_count,
            'chunk_count': DocumentChunk.query.filter_by(document_id=self.id).count()
        }

class DocumentChunk(db.Model):
    """Model for storing text chunks from documents with their embeddings"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    
    # Store embedding as JSON string (for simple storage)
    embedding_json = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_embedding(self):
        """Get embedding as list of floats"""
        if self.embedding_json:
            return json.loads(self.embedding_json)
        return None
    
    def set_embedding(self, embedding):
        """Set embedding from list of floats"""
        self.embedding_json = json.dumps(embedding)
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'page_number': self.page_number,
            'text_content': self.text_content[:200] + '...' if len(self.text_content) > 200 else self.text_content,
            'has_embedding': bool(self.embedding_json),
            'created_at': self.created_at.isoformat()
        }

class ChatHistory(db.Model):
    """Model for storing chat conversations"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    
    # References to documents used in the response
    referenced_documents = db.Column(db.Text)  # JSON array of document IDs
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_referenced_documents(self):
        """Get referenced document IDs as list"""
        if self.referenced_documents:
            return json.loads(self.referenced_documents)
        return []
    
    def set_referenced_documents(self, doc_ids):
        """Set referenced document IDs from list"""
        self.referenced_documents = json.dumps(doc_ids)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'referenced_documents': self.get_referenced_documents(),
            'created_at': self.created_at.isoformat()
        }