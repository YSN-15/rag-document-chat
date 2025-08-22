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
            
            # Store the full content directly in the document
            document.content = extracted_data['content']
            document.page_count = extracted_data.get('page_count', 1)
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
            # Get all indexed documents for this session
            documents_query = Document.query.filter_by(
                session_id=session_id, 
                status='indexed'
            )
            
            # Apply document filters if specified
            if document_filters and 'document_names' in document_filters:
                documents_query = documents_query.filter(
                    Document.original_filename.in_(document_filters['document_names'])
                )
            
            documents = documents_query.all()
            
            if not documents:
                return {
                    "response": "I couldn't find any indexed documents to answer this question. Please upload and process some documents first.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Combine all document content
            full_context = ""
            sources = []
            
            for doc in documents:
                if doc.content:
                    full_context += f"\n--- Document: {doc.original_filename} ---\n"
                    full_context += doc.content + "\n"
                    
                    sources.append({
                        'document_name': doc.original_filename,
                        'page_count': doc.page_count or 1
                    })
            
            if not full_context.strip():
                return {
                    "response": "No content found in the indexed documents.",
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
