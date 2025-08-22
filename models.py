from app import db
from datetime import datetime
from sqlalchemy import Text

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='uploaded')  # uploaded, processing, indexed, error
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime)
    session_id = db.Column(db.String(100), nullable=False)
    content = db.Column(Text)
    page_count = db.Column(db.Integer, default=0)
    error_message = db.Column(Text)
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(Text, nullable=False)
    page_number = db.Column(db.Integer)
    section = db.Column(db.String(500))
    azure_search_id = db.Column(db.String(100), unique=True)
    
    document = db.relationship('Document', backref=db.backref('chunks', lazy=True))
    
    def __repr__(self):
        return f'<DocumentChunk {self.azure_search_id}>'

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatSession {self.session_id}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    message_type = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.Column(Text)  # JSON string of source documents
    
    def __repr__(self):
        return f'<ChatMessage {self.session_id} - {self.message_type}>'
