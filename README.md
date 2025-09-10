A Flask web application that implements a simplified Retrieval-Augmented Generation (RAG) system using Azure AI Document Intelligence for text extraction and GROQ LLM for intelligent question answering.
## Features
🔍 **Document Processing**: Upload PDF, DOCX, TXT, PNG, and JPG files  
🧠 **AI Text Extraction**: Azure Document Intelligence extracts text, tables, and key-value pairs  
💬 **Smart Q&A**: Ask questions about your documents using GROQ's Llama 3.1 model  
📱 **Responsive UI**: Bootstrap-based interface with dark/light theme support  
🔒 **Session-based**: Each user gets isolated document storage and chat history  
## Architecture
Upload Document → Azure Document Intelligence → Extract Text → Store in Session → GROQ LLM → Generate Answer

**Simple & Efficient**: No complex search infrastructure - documents are processed once and stored in memory for direct querying.
## Prerequisites
- Python 3.11+
- Azure Document Intelligence account
- GROQ API account
## Environment Variables
Create these environment variables in your deployment platform:

# Azure Document Intelligence
AZURE_DI_ENDPOINT=your_azure_document_intelligence_endpoint
AZURE_DI_KEY=your_azure_document_intelligence_key
# GROQ API
GROQ_API_KEY=your_groq_api_key
# Database (optional - defaults to SQLite)
DATABASE_URL=your_database_url
# Flask Security
SESSION_SECRET=your_session_secret_key
Installation & Setup
Clone the repository

git clone https://github.com/yourusername/rag-document-chat.git
cd rag-document-chat
Install dependencies

pip install -r requirements.txt
Set environment variables

Copy .env.example to .env
Fill in your API keys and endpoints
Run the application

python main.py
Access the app

Open http://localhost:5000
Upload documents and start chatting!
Getting API Keys
Azure Document Intelligence
Go to Azure Portal
Create a "Document Intelligence" resource
Copy the endpoint and key from the resource overview
GROQ API
Sign up at GROQ Console
Generate an API key from the dashboard
Copy the API key
Usage
Upload Documents
Click "Upload Documents" on the homepage
Drag and drop or select files (PDF, DOCX, TXT, PNG, JPG)
Wait for processing to complete (green checkmark appears)
Ask Questions
Go to the "Chat" section
Type questions about your uploaded documents
Get AI-powered answers with document citations
Example Questions
"What is the main topic of this document?"
"Summarize the key points in 50 words"
"What are the dates mentioned in the insurance form?"
"Extract all the amounts from the financial document"
Project Structure
├── app.py                  # Flask application setup
├── main.py                # Application entry point
├── models.py              # Database models
├── config.py              # Configuration settings
├── routes/
│   ├── main.py           # Home page routes
│   ├── documents.py      # Document upload/management
│   └── chat.py           # Chat interface
├── services/
│   ├── document_intelligence.py  # Azure DI integration
│   ├── document_processor.py     # Document processing logic
│   └── groq_llm.py              # GROQ LLM integration
├── templates/            # HTML templates
├── static/              # CSS, JS, images
└── uploads/             # Temporary file storage
Technology Stack
Backend:

Flask (Python web framework)
SQLAlchemy (Database ORM)
Azure AI Document Intelligence (Text extraction)
GROQ API (Language model)
Frontend:

Bootstrap 5.3 (UI framework)
Bootstrap Icons (Icon library)
Vanilla JavaScript
Storage:

SQLite (default database)
Session-based document content storage
Local file system for temporary uploads
Features in Detail
Document Processing
Multi-format Support: PDF, DOCX, TXT, PNG, JPG
OCR Capability: Extract text from images using Azure DI
Structure Extraction: Tables, key-value pairs, and formatted text
Session Isolation: Each user's documents are kept separate
AI Integration
Azure Document Intelligence: Professional-grade text extraction
GROQ Llama 3.1: Fast, accurate language model responses
Context-aware: Full document content provided to AI for accurate answers
Citation Support: Responses include document name references
User Experience
Drag-and-drop Upload: Intuitive file upload interface
Real-time Processing: Live status updates during document processing
Responsive Design: Works on desktop, tablet, and mobile
Theme Support: Light and dark mode toggle
