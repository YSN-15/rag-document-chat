# Overview

This is a Flask web application implementing a Retrieval-Augmented Generation (RAG) system using Azure AI services and GROQ LLM. The application allows users to upload documents (PDF, DOCX, TXT, PNG, JPG), processes them using Azure Document Intelligence for text extraction, indexes the content in Azure AI Search, and provides a chat interface where users can ask questions about their uploaded documents. The system generates contextual responses using GROQ's Mixtral model, citing specific sources and page numbers from the indexed documents.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Flask Web Application Structure
The application follows a modular Flask architecture with blueprints for route organization:
- **Main Blueprint**: Handles home page and theme toggling
- **Documents Blueprint**: Manages file upload, processing, and document listing
- **Chat Blueprint**: Provides chat interface and question-answering functionality

## Document Processing Pipeline
The system implements a multi-stage document processing workflow:
1. **File Upload**: Supports multiple formats with file validation and size limits
2. **Document Intelligence**: Uses Azure Document Intelligence for text extraction, OCR, and structure analysis
3. **Content Chunking**: Splits documents into semantic chunks (1000 tokens max) with overlap for context preservation
4. **Search Indexing**: Stores processed chunks in Azure AI Search with metadata

## Database Design
Uses SQLAlchemy with Flask for ORM with four main models:
- **Document**: Tracks uploaded files, processing status, and metadata
- **DocumentChunk**: Stores individual text chunks with page numbers and search IDs
- **ChatSession**: Manages user sessions for document isolation
- **ChatMessage**: Stores chat history with source citations

## Session Management
Implements UUID-based session management to isolate user documents and chat history without requiring user authentication. Each user gets a unique session ID stored in Flask sessions.

## Frontend Architecture
Bootstrap-based responsive UI with:
- Drag-and-drop file upload interface
- Document status tracking with visual indicators
- Chat interface with message history
- Theme switching (light/dark mode)
- Real-time processing status updates

# External Dependencies

## Azure AI Services
- **Azure Document Intelligence**: For document analysis, text extraction, and OCR processing of images
- **Azure AI Search**: Vector and keyword search index for document chunks with metadata

## GROQ LLM Integration
- **GROQ API**: Uses Mixtral-8x7b-32768 model for generating contextual responses
- **Response Generation**: Combines search results with structured prompts for accurate, cited answers

## Database
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Default database (configurable to other SQL databases via DATABASE_URL)

## Frontend Libraries
- **Bootstrap 5.3**: UI framework with dark/light theme support
- **Bootstrap Icons**: Icon library for consistent UI elements

## File Processing
- **Werkzeug**: File upload handling and security utilities
- **Secure filename generation**: Protection against path traversal attacks

## Configuration Management
Environment-based configuration system supporting:
- Azure service credentials and endpoints
- File upload limits and allowed extensions
- Chunking parameters and search settings
- Flask security configuration