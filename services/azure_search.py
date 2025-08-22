import json
import logging
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from azure.core.credentials import AzureKeyCredential
from config import Config

logger = logging.getLogger(__name__)

class AzureSearchService:
    def __init__(self):
        self.endpoint = Config.AZURE_SEARCH_ENDPOINT
        self.key = Config.AZURE_SEARCH_KEY
        self.index_name = Config.AZURE_SEARCH_INDEX
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure Search credentials not configured")
        
        self.credential = AzureKeyCredential(self.key)
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        # Initialize index
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """
        Ensure the search index exists with the correct schema
        """
        try:
            # Try to get existing index
            try:
                self.index_client.get_index(self.index_name)
                logger.info(f"Index {self.index_name} already exists")
                return
            except Exception:
                logger.info(f"Index {self.index_name} does not exist, creating...")
            
            # Create index schema
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
                SimpleField(name="document_name", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True),
                SimpleField(name="section", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
                SimpleField(name="upload_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
                SimpleField(name="session_id", type=SearchFieldDataType.String, filterable=True)
            ]
            
            index = SearchIndex(name=self.index_name, fields=fields)
            self.index_client.create_index(index)
            logger.info(f"Created index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error ensuring index exists: {str(e)}")
            raise
    
    def index_document_chunks(self, chunks_data):
        """
        Index document chunks in Azure Search
        chunks_data: list of dictionaries with chunk information
        """
        try:
            documents = []
            for chunk_data in chunks_data:
                doc = {
                    "id": chunk_data["id"],
                    "content": chunk_data["content"],
                    "document_name": chunk_data["document_name"],
                    "document_id": str(chunk_data["document_id"]),
                    "page_number": chunk_data.get("page_number", 1),
                    "section": chunk_data.get("section", ""),
                    "chunk_index": chunk_data["chunk_index"],
                    "upload_date": chunk_data["upload_date"],
                    "session_id": chunk_data["session_id"]
                }
                documents.append(doc)
            
            # Upload documents in batches
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                result = self.search_client.upload_documents(documents=batch)
                
                # Check for errors
                for item in result:
                    if not item.succeeded:
                        logger.error(f"Failed to index document {item.key}: {item.error_message}")
                        raise Exception(f"Indexing failed for document {item.key}")
            
            logger.info(f"Successfully indexed {len(documents)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise
    
    def search_documents(self, query, session_id=None, document_filters=None, top_k=None):
        """
        Search for relevant document chunks
        """
        try:
            top_k = top_k or Config.TOP_K_RESULTS
            
            # Build search parameters
            search_params = {
                "search_text": query,
                "top": top_k,
                "include_total_count": True
            }
            
            # Add filters
            filters = []
            if session_id:
                filters.append(f"session_id eq '{session_id}'")
            
            if document_filters:
                if 'document_names' in document_filters:
                    doc_filters = " or ".join([f"document_name eq '{name}'" for name in document_filters['document_names']])
                    filters.append(f"({doc_filters})")
            
            if filters:
                search_params["filter"] = " and ".join(filters)
            
            # Perform search
            results = self.search_client.search(**search_params)
            
            # Process results
            search_results = []
            for result in results:
                search_results.append({
                    "id": result["id"],
                    "content": result["content"],
                    "document_name": result["document_name"],
                    "page_number": result.get("page_number", 1),
                    "section": result.get("section", ""),
                    "chunk_index": result["chunk_index"],
                    "score": result.get("@search.score", 0)
                })
            
            logger.info(f"Search returned {len(search_results)} results for query: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
    
    def delete_document_chunks(self, document_id):
        """
        Delete all chunks for a specific document
        """
        try:
            # Search for all chunks of the document
            results = self.search_client.search(
                search_text="*",
                filter=f"document_id eq '{document_id}'"
            )
            
            # Delete found chunks
            documents_to_delete = []
            for result in results:
                documents_to_delete.append({"id": result["id"]})
            
            if documents_to_delete:
                self.search_client.delete_documents(documents=documents_to_delete)
                logger.info(f"Deleted {len(documents_to_delete)} chunks for document {document_id}")
            
            return len(documents_to_delete)
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise
