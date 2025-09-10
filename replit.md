# Pilot RAG - Automotive Document Assistant

## Overview

This is a sophisticated RAG (Retrieval-Augmented Generation) system specifically designed for automotive document analysis. The application allows users to upload automotive PDF documents (manuals, guides, technical specifications) and then ask natural language questions about their content. The system combines intelligent document search with AI-powered responses to provide accurate, contextual answers based on the uploaded documentation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Interface**: Bootstrap-based responsive design with dark theme optimized for document management
- **Document Management**: Drag-and-drop PDF upload with progress indicators and document listing
- **Chat Interface**: Real-time conversation system with rich text formatting and document references
- **UI Framework**: Bootstrap 5 with custom automotive-focused styling
- **Client-side Logic**: Vanilla JavaScript handling file uploads, chat interactions, and document management

### Backend Architecture
- **Web Framework**: Flask application with SQLAlchemy ORM for database operations
- **Document Processing**: PDF text extraction using PyPDF2 with intelligent text chunking
- **Vector Search**: TF-IDF vectorization with cosine similarity for document retrieval
- **RAG System**: Retrieval-Augmented Generation combining document search with AI responses
- **API Integration**: OpenRouter client optimized for automotive-focused conversations
- **Session Management**: Secure server-side session storage for API keys and conversation history
- **Database Layer**: SQLAlchemy with declarative base for document and conversation persistence

### Data Storage
- **Primary Database**: PostgreSQL (production) / SQLite (development) via DATABASE_URL configuration
- **Connection Pooling**: Configured with pool recycling and pre-ping for connection health
- **Document Storage**: File system storage for uploaded PDFs with secure filename generation
- **Vector Storage**: In-memory TF-IDF vectors with database-backed text chunks
- **Models**: Document, DocumentChunk, and ChatHistory models for comprehensive data management

### Security and Safety
- **Document Upload Security**: File type validation, size limits (16MB), and secure filename generation
- **Session Isolation**: Server-side secure session storage with UUID-based identification
- **API Key Protection**: Never expose API keys to client-side code or browser storage
- **Content Filtering**: Dual-layer automotive topic enforcement (keyword + LLM-level)
- **File Storage Security**: Isolated upload directory with automatic cleanup capabilities
- **Proxy Support**: ProxyFix middleware for handling reverse proxy headers

### RAG Integration Strategy
- **Document Ingestion**: Multi-step PDF processing with text extraction and chunking
- **Vector Search Engine**: TF-IDF vectorization for semantic document retrieval
- **Context Assembly**: Dynamic context building from multiple relevant document chunks
- **AI Integration**: OpenRouter client with automotive system prompts and conversation memory
- **Response Enhancement**: Document citations and relevance scoring in AI responses
- **Session-based Configuration**: API keys, model preferences, and conversation history stored securely

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy integration
- **SQLAlchemy**: Database ORM with declarative base pattern for document and conversation storage
- **Werkzeug**: WSGI utilities including ProxyFix middleware and secure filename handling

### Document Processing Dependencies
- **PyPDF2**: PDF text extraction and page processing
- **scikit-learn**: TF-IDF vectorization and cosine similarity calculations
- **NumPy**: Numerical operations for vector mathematics

### Frontend Dependencies
- **Bootstrap 5**: UI framework with custom dark theme for document management
- **Feather Icons**: Icon library for UI elements
- **Vanilla JavaScript**: File upload, drag-and-drop, and chat interface functionality

### API Services
- **OpenRouter**: Primary external service for AI model API access
- **Multiple AI Models**: Support for various models including OpenAI GPT, Claude, and others through OpenRouter

### Development and Storage
- **Requests Library**: HTTP client for OpenRouter API communications
- **File System**: PDF storage with secure upload directory management
- **Logging**: Built-in Python logging for debugging and monitoring

### Environment Configuration
- **DATABASE_URL**: Configurable database connection string (PostgreSQL/SQLite)
- **OPENROUTER_API_KEY**: API key for OpenRouter service access
- **SESSION_SECRET**: Flask session encryption key
- **Upload Configuration**: MAX_CONTENT_LENGTH and UPLOAD_FOLDER settings