# Python IDE for OpenRouter

## Overview

This is a web-based Python IDE specifically designed for testing and interacting with OpenRouter APIs. The application provides a Monaco-based code editor where users can write Python code, execute it in a sandboxed environment, and test OpenRouter API calls with various AI models. The IDE features code snippet management, real-time code execution with output display, and a user-friendly interface for configuring API settings.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Interface**: Built with Bootstrap and custom CSS using a dark theme optimized for coding
- **Code Editor**: Monaco Editor integration for syntax highlighting, auto-completion, and Python code editing
- **UI Framework**: Bootstrap 5 with Replit dark theme for consistent styling
- **Client-side Logic**: Vanilla JavaScript handling editor interactions, API calls, and UI updates

### Backend Architecture
- **Web Framework**: Flask application with SQLAlchemy ORM for database operations
- **Code Execution**: Sandboxed Python code execution using subprocess with timeout protection and temporary file handling
- **API Integration**: Dedicated OpenRouter client for making API calls to various AI models
- **Session Management**: Flask sessions for storing user preferences and API keys
- **Database Layer**: SQLAlchemy with declarative base for ORM operations

### Data Storage
- **Primary Database**: SQLite by default (configurable via DATABASE_URL environment variable)
- **Connection Pooling**: Configured with pool recycling and pre-ping for connection health
- **Models**: CodeSnippet model for storing and managing reusable code snippets with timestamps

### Security and Safety
- **Code Execution Sandbox**: Isolated subprocess execution with 30-second timeout limits
- **Temporary File Management**: Automatic cleanup of temporary files after code execution
- **Environment Isolation**: Code runs in separate processes with controlled environment variables
- **Proxy Support**: ProxyFix middleware for handling reverse proxy headers

### API Integration Strategy
- **OpenRouter Client**: Abstracted client for interacting with OpenRouter's chat completion API
- **Model Flexibility**: Support for multiple AI models through configurable model selection
- **Error Handling**: Comprehensive error handling for API failures and timeouts
- **Session-based Configuration**: API keys and model preferences stored in user sessions

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy integration
- **SQLAlchemy**: Database ORM with declarative base pattern
- **Werkzeug**: WSGI utilities including ProxyFix middleware

### Frontend Dependencies
- **Monaco Editor**: Feature-rich code editor with Python syntax highlighting
- **Bootstrap 5**: UI framework with Replit dark theme
- **Feather Icons**: Icon library for UI elements

### API Services
- **OpenRouter**: Primary external service for AI model API access
- **Multiple AI Models**: Support for various models including OpenAI GPT, Claude, and others through OpenRouter

### Development and Execution
- **Python Subprocess**: For isolated code execution
- **Requests Library**: HTTP client for external API communications
- **Logging**: Built-in Python logging for debugging and monitoring

### Environment Configuration
- **DATABASE_URL**: Configurable database connection string
- **OPENROUTER_API_KEY**: API key for OpenRouter service access
- **SESSION_SECRET**: Flask session encryption key