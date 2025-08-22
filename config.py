import os

class Config:
    # Azure Document Intelligence
    AZURE_DI_ENDPOINT = os.environ.get("AZURE_DI_ENDPOINT")
    AZURE_DI_KEY = os.environ.get("AZURE_DI_KEY")
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
    AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "documents")
    
    # GROQ API
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    
    # Flask Config
    FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 10485760))  # 10MB
    ALLOWED_EXTENSIONS = set(os.environ.get("ALLOWED_EXTENSIONS", "pdf,docx,txt,png,jpg").split(','))
    
    # Chunking settings
    MAX_CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Search settings
    TOP_K_RESULTS = 5
    MIN_RELEVANCE_SCORE = 0.5
