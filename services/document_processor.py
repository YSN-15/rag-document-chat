import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from services.document_intelligence import DocumentIntelligenceService
from services.groq_llm import GroqLLMService
from models import Document
from app import db

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.doc_intelligence = DocumentIntelligenceService()
        self.llm_service = GroqLLMService()
    
    def process_uploaded_file(self, file, session_id):
        """
        Process an uploaded file through the complete pipeline
        """
        document = None
        file_path = None
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
            
            # Create document record
            document = Document()
            document.filename = filename
            document.original_filename = file.filename
            document.file_path = file_path
            document.file_size = os.path.getsize(file_path)
            document.mime_type = file.content_type or 'application/octet-stream'
            document.session_id = session_id
            document.status = 'processing'
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"Processing document: {file.filename}")
            
            # Extract content based on file type
            if self._is_image_file(filename):
                extracted_data = self.doc_intelligence.extract_text_from_image(file_path)
            else:
                extracted_data = self.doc_intelligence.analyze_document(file_path)
            
            # Store extracted content in session for immediate use
            from flask import session
            if 'documents_content' not in session:
                session['documents_content'] = {}
            
            session['documents_content'][str(document.id)] = {
                'content': extracted_data['content'],
                'filename': document.original_filename,
                'page_count': extracted_data.get('page_count', 1)
            }
            
            # Update document status only
            document.status = 'indexed'
            document.processed_date = datetime.utcnow()
            db.session.commit()
            
            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary file {file_path}: {e}")
            
            logger.info(f"Successfully processed document: {file.filename}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing document {file.filename}: {str(e)}")
            
            # Update document status to error
            if document is not None:
                document.status = 'error'
                document.error_message = str(e)
                db.session.commit()
            
            # Clean up temporary file
            if file_path is not None and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            
            raise
    
    
    def _is_image_file(self, filename):
        """
        Check if file is an image that requires OCR
        """
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def search_and_answer(self, query, session_id, document_filters=None):
        """
        Answer question using full document content with LLM
        """
        try:
            from flask import session
            
            # Get document content from session
            documents_content = session.get('documents_content', {})
            
            if not documents_content:
                return {
                    "response": "I couldn't find any documents to answer this question. Please upload and process some documents first.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Get indexed documents from database to check which ones are ready
            indexed_docs = Document.query.filter_by(
                session_id=session_id, 
                status='indexed'
            ).all()
            
            if not indexed_docs:
                return {
                    "response": "No documents have been processed yet. Please wait for processing to complete.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Combine all document content from session
            full_context = ""
            sources = []
            
            for doc in indexed_docs:
                doc_content = documents_content.get(str(doc.id))
                if doc_content:
                    # Apply document filters if specified
                    if document_filters and 'document_names' in document_filters:
                        if doc.original_filename not in document_filters['document_names']:
                            continue
                    
                    full_context += f"\n--- Document: {doc.original_filename} ---\n"
                    full_context += doc_content['content'] + "\n"
                    
                    sources.append({
                        'document_name': doc.original_filename,
                        'page_count': doc_content.get('page_count', 1)
                    })
            
            if not full_context.strip():
                return {
                    "response": "No content found in the processed documents.",
                    "sources": sources,
                    "context_used": 0
                }
            
            # Generate response using LLM with full context
            llm_response = self.llm_service.generate_response_from_context(query, full_context, sources)
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error in search and answer: {str(e)}")
            raise
    
    def delete_document(self, document_id, session_id):
        """
        Delete a document
        """
        try:
            document = Document.query.filter_by(id=document_id, session_id=session_id).first()
            if not document:
                raise ValueError("Document not found")
            
            # Delete document from database
            db.session.delete(document)
            db.session.commit()
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            db.session.rollback()
            raise
