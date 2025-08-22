import os
from flask import Blueprint, request, render_template, jsonify, session, flash, redirect, url_for
from werkzeug.utils import secure_filename
from models import Document
from services.document_processor import DocumentProcessor
import uuid

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    from app import app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/')
def list_documents():
    # Ensure user has a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    documents = Document.query.filter_by(session_id=session_id).order_by(Document.upload_date.desc()).all()
    
    return render_template('documents.html', documents=documents)

@documents_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('main.index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('main.index'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed. Supported types: PDF, DOCX, TXT, PNG, JPG', 'error')
            return redirect(url_for('main.index'))
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        from app import app
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            flash('File too large. Maximum size: 10MB', 'error')
            return redirect(url_for('main.index'))
        
        # Process the document
        processor = DocumentProcessor()
        document = processor.process_uploaded_file(file, session_id)
        
        flash(f'Document "{document.original_filename}" uploaded and processed successfully!', 'success')
        return redirect(url_for('documents.list_documents'))
        
    except Exception as e:
        flash(f'Error processing document: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@documents_bp.route('/delete/<int:document_id>', methods=['POST'])
def delete_document(document_id):
    if 'session_id' not in session:
        return jsonify({'error': 'No session'}), 400
    
    session_id = session['session_id']
    
    try:
        processor = DocumentProcessor()
        processor.delete_document(document_id, session_id)
        
        flash('Document deleted successfully', 'success')
        return redirect(url_for('documents.list_documents'))
        
    except Exception as e:
        flash(f'Error deleting document: {str(e)}', 'error')
        return redirect(url_for('documents.list_documents'))

@documents_bp.route('/status/<int:document_id>')
def document_status(document_id):
    if 'session_id' not in session:
        return jsonify({'error': 'No session'}), 400
    
    session_id = session['session_id']
    document = Document.query.filter_by(id=document_id, session_id=session_id).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    return jsonify({
        'status': document.status,
        'total_chunks': document.total_chunks,
        'error_message': document.error_message
    })
