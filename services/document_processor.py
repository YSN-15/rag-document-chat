import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from services.document_intelligence import DocumentIntelligenceService
from services.azure_search import AzureSearchService
from services.groq_llm import GroqLLMService
from models import Document, DocumentChunk
from app import db
from config import Config

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.doc_intelligence = DocumentIntelligenceService()
        self.search_service = AzureSearchService()
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
            
            # Chunk the document
            chunks = self._chunk_document(extracted_data, document.id)
            
            # Create chunk records
            chunk_objects = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document.id}_{i}"
                chunk_obj = DocumentChunk()
                chunk_obj.document_id = document.id
                chunk_obj.chunk_index = i
                chunk_obj.content = chunk['content']
                chunk_obj.page_number = chunk.get('page_number', 1)
                chunk_obj.section = chunk.get('section', '')
                chunk_obj.azure_search_id = chunk_id
                chunk_objects.append(chunk_obj)
                db.session.add(chunk_obj)
            
            # Update document with chunk count
            document.total_chunks = len(chunks)
            db.session.commit()
            
            # Prepare data for Azure Search
            search_chunks = []
            for chunk_obj in chunk_objects:
                search_chunks.append({
                    "id": chunk_obj.azure_search_id,
                    "content": chunk_obj.content,
                    "document_name": document.original_filename,
                    "document_id": document.id,
                    "page_number": chunk_obj.page_number,
                    "section": chunk_obj.section,
                    "chunk_index": chunk_obj.chunk_index,
                    "upload_date": document.upload_date.isoformat(),
                    "session_id": session_id
                })
            
            # Index in Azure Search
            self.search_service.index_document_chunks(search_chunks)
            
            # Update document status
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
    
    def _chunk_document(self, extracted_data, document_id):
        """
        Split document content into semantic chunks
        """
        chunks = []
        max_chunk_size = Config.MAX_CHUNK_SIZE
        overlap_size = Config.CHUNK_OVERLAP
        
        # Process each page
        for page in extracted_data.get('pages', []):
            page_content = page['content']
            page_number = page['page_number']
            
            # Split content into sentences for better semantic chunking
            sentences = self._split_into_sentences(page_content)
            
            current_chunk = ""
            current_chunk_sentences = []
            
            for sentence in sentences:
                # Check if adding this sentence would exceed the limit
                potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(potential_chunk.split()) <= max_chunk_size:
                    current_chunk = potential_chunk
                    current_chunk_sentences.append(sentence)
                else:
                    # Save current chunk if it has content
                    if current_chunk.strip():
                        chunks.append({
                            'content': current_chunk.strip(),
                            'page_number': page_number,
                            'section': self._extract_section_header(current_chunk_sentences)
                        })
                    
                    # Start new chunk with overlap
                    overlap_sentences = current_chunk_sentences[-2:] if len(current_chunk_sentences) > 2 else current_chunk_sentences
                    current_chunk = " ".join(overlap_sentences + [sentence])
                    current_chunk_sentences = overlap_sentences + [sentence]
            
            # Add remaining content as a chunk
            if current_chunk.strip():
                chunks.append({
                    'content': current_chunk.strip(),
                    'page_number': page_number,
                    'section': self._extract_section_header(current_chunk_sentences)
                })
        
        # If no pages were processed, create chunks from the main content
        if not chunks and extracted_data.get('content'):
            content = extracted_data['content']
            words = content.split()
            
            for i in range(0, len(words), max_chunk_size - overlap_size):
                chunk_words = words[i:i + max_chunk_size]
                chunk_content = " ".join(chunk_words)
                
                chunks.append({
                    'content': chunk_content,
                    'page_number': 1,
                    'section': ''
                })
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        return chunks
    
    def _split_into_sentences(self, text):
        """
        Split text into sentences for better chunking
        """
        # Simple sentence splitting on periods, exclamation marks, and question marks
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_section_header(self, sentences):
        """
        Try to extract section header from the beginning of chunks
        """
        if not sentences:
            return ""
        
        first_sentence = sentences[0]
        # Look for common header patterns (short lines, all caps, etc.)
        if len(first_sentence.split()) <= 5 and (first_sentence.isupper() or first_sentence.istitle()):
            return first_sentence
        
        return ""
    
    def _is_image_file(self, filename):
        """
        Check if file is an image that requires OCR
        """
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def search_and_answer(self, query, session_id, document_filters=None):
        """
        Search documents and generate answer using LLM
        """
        try:
            # Search for relevant documents
            search_results = self.search_service.search_documents(
                query=query,
                session_id=session_id,
                document_filters=document_filters,
                top_k=Config.TOP_K_RESULTS
            )
            
            if not search_results:
                return {
                    "response": "I couldn't find any relevant information in your uploaded documents to answer this question.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Generate response using LLM
            llm_response = self.llm_service.generate_response(query, search_results)
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error in search and answer: {str(e)}")
            raise
    
    def delete_document(self, document_id, session_id):
        """
        Delete a document and all its chunks
        """
        try:
            document = Document.query.filter_by(id=document_id, session_id=session_id).first()
            if not document:
                raise ValueError("Document not found")
            
            # Delete from Azure Search
            deleted_chunks = self.search_service.delete_document_chunks(document_id)
            
            # Delete chunks from database
            DocumentChunk.query.filter_by(document_id=document_id).delete()
            
            # Delete document from database
            db.session.delete(document)
            db.session.commit()
            
            logger.info(f"Deleted document {document_id} and {deleted_chunks} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            db.session.rollback()
            raise
