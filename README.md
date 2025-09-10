# Automotive Chat Assistant

A sophisticated web-based AI chat assistant specialized exclusively in automotive topics. Built with Flask, OpenRouter API integration, and featuring secure conversation memory with intelligent content filtering.

## 🚗 Overview

This application transforms a general-purpose AI chat interface into a focused automotive expert that only discusses cars, engines, maintenance, manufacturers, and related automotive topics. The system includes robust conversation memory, secure API key management, and dual-layer content filtering.

## ✨ Key Features

### 🤖 **Automotive-Focused AI**
- **LLM-Level System Prompt**: Programs the AI to be an automotive expert
- **Dual-Layer Content Filtering**: Frontend keyword detection + AI-level topic control
- **Intelligent Redirection**: Politely redirects off-topic questions back to automotive discussions
- **75+ Automotive Keywords**: Comprehensive filtering including conversational terms

### 💬 **Advanced Conversation Memory**
- **Multi-Turn Conversations**: Remembers context across multiple messages
- **Session-Based History**: Maintains conversation state per user session
- **Smart Truncation**: Automatically manages conversation length (20 messages max)
- **Error Recovery**: Conversation history rollback on API failures

### 🔒 **Enterprise-Grade Security**
- **Server-Side Storage**: API keys never stored in client cookies
- **Secure Session Management**: UUID-based session identification
- **Masked Key Display**: Frontend shows `••••••••••••••••` instead of actual keys
- **No Client Exposure**: Sensitive data isolated from browser access

### 🎨 **Rich User Experience**
- **Monaco-Style Dark Theme**: Professional coding interface aesthetic
- **Rich Text Formatting**: Bold, italic, bullet points, numbered lists
- **Real-Time Responses**: Live typing indicators and response formatting
- **Bootstrap UI**: Responsive design with Feather icons
- **Error Handling**: Graceful failure recovery with user-friendly messages

### ⚡ **Robust API Integration**
- **OpenRouter Support**: Integration with multiple AI models
- **Timeout Protection**: Multiple layers (15s API, 30s worker, system alarms)
- **Rate Limit Handling**: Graceful 429 error management
- **Production Headers**: Dynamic domain detection for deployment

## 🏗️ Architecture

### **Backend (Python/Flask)**
```
app.py              # Flask application setup and configuration
routes.py           # API endpoints and conversation logic
openrouter_client.py # OpenRouter API client with automotive system prompt
models.py           # Database models (SQLAlchemy)
main.py             # Application entry point
```

### **Frontend (HTML/CSS/JavaScript)**
```
templates/index.html    # Main chat interface
static/css/custom.css   # Dark theme and chat styling
static/js/editor.js     # Chat functionality and API calls
```

### **Security Architecture**
```
Client Session Cookie → Secure Session ID (UUID)
                     ↓
Server-Side Storage → {
    api_key: "actual_key",
    model: "selected_model", 
    chat_history: [conversation_array]
}
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- OpenRouter API key

### Environment Variables
```bash
SESSION_SECRET=your_secret_key_here
DATABASE_URL=postgresql://user:password@host:port/database
OPENROUTER_API_KEY=your_openrouter_key_here  # Optional
```

### Installation
```bash
# Install UV package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies using UV
uv sync

# Or install manually with pip
pip install flask flask-sqlalchemy gunicorn psycopg2-binary requests werkzeug email-validator

# Run the application
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### Usage
1. **Configure API Key**: Go to Settings and enter your OpenRouter API key
2. **Start Chatting**: Ask any automotive-related question
3. **Conversation Memory**: Follow up with questions that reference previous discussion
4. **Content Filtering**: Try asking non-automotive questions to see intelligent redirection

## 🔧 Technical Implementation

### Conversation Memory System
```python
# Session-based conversation storage
conversation_history = [
    {"role": "user", "content": "What oil should I use for my Honda Civic?"},
    {"role": "assistant", "content": "For Honda Civics, I recommend..."},
    {"role": "user", "content": "How often should I change it?"},  # Remembers context
    {"role": "assistant", "content": "For the oil we just discussed..."}
]
```

### Content Filtering Pipeline
1. **Frontend Keywords**: 75+ automotive terms including casual conversation words
2. **LLM System Prompt**: Automotive expert persona with topic enforcement
3. **Graceful Redirection**: Polite responses for off-topic queries

### Security Features
- **Server-Side Session Storage**: `secure_sessions[uuid] = {api_key, history}`
- **Masked Client Display**: Never expose actual API keys to frontend
- **Session Isolation**: Each user gets unique conversation context
- **Automatic Cleanup**: Error recovery removes failed messages

## 📊 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main chat interface |
| `/chat` | POST | Send message and get AI response |
| `/test_openrouter` | POST | Test API connection |
| `/get_session_data` | GET | Get session info (masked) |
| `/clear_session` | POST | Clear all session data |
| `/clear_chat` | POST | Clear conversation history |

## 🔍 Code Highlights

### Automotive System Prompt
```python
system_prompt = """You are an automotive expert assistant. You ONLY discuss topics related to:
- Cars, trucks, motorcycles, and other vehicles
- Automotive technology, engines, and mechanical systems
- Vehicle maintenance, repair, and troubleshooting
- Car manufacturers, models, and automotive history
- Racing, motorsports, and automotive performance
- Electric vehicles, hybrids, and automotive innovations
- Vehicle safety, regulations, and automotive industry news

If someone asks about anything outside automotive topics, politely redirect them back to car-related discussions."""
```

### Secure Session Management
```python
def get_secure_session_data(session_id):
    if session_id not in secure_sessions:
        secure_sessions[session_id] = {
            'api_key': '',
            'model': 'deepseek/deepseek-chat-v3-0324:free',
            'chat_history': []
        }
    return secure_sessions[session_id]
```

### Conversation Memory with Error Recovery
```python
# Add user message
conversation_history.append({'role': 'user', 'content': message})

try:
    response = client.chat_completion(model, conversation_history)
    # Add AI response on success
    conversation_history.append({'role': 'assistant', 'content': response['content']})
except Exception:
    # Remove user message on failure to maintain consistency
    conversation_history.pop()
```

## 🎯 Project Evolution

This project evolved from a failing Python IDE for OpenRouter APIs into a specialized automotive chat assistant:

1. **Phase 1**: Fixed deployment issues and API integration
2. **Phase 2**: Removed Python IDE functionality, focused on chat
3. **Phase 3**: Added automotive content filtering and topic enforcement
4. **Phase 4**: Implemented conversation memory and secure session management
5. **Phase 5**: Enhanced security with server-side storage and masked keys

## 🛡️ Security Considerations

### Current Security Features
- ✅ Server-side API key storage
- ✅ No client-side secret exposure
- ✅ Session-based conversation isolation
- ✅ Input validation and error handling
- ✅ Timeout protection against hanging requests

### Production Recommendations (Not Yet Implemented)
- 🔄 **CSRF Protection**: Currently no CSRF protection on POST endpoints
- 🔄 **Rate Limiting**: No rate limiting implemented - potential for abuse
- 🔄 **Persistent Sessions**: Currently uses in-memory storage (lost on restart)
- 🔄 **Session TTL**: No automatic session cleanup
- 🔄 **Multi-Worker Support**: Sessions won't work with multiple Gunicorn workers

## 📈 Performance & Scalability

### Current Capabilities
- **Single Worker**: Optimized for development and testing
- **In-Memory Sessions**: Fast access, but not persistent across restarts
- **20-Message History**: Balanced between context and token efficiency
- **15-Second Timeouts**: Prevents worker blocking

### Scaling Considerations
- Use Redis for shared session storage across workers
- Implement conversation summarization for longer contexts
- Add connection pooling for database operations
- Consider CDN for static assets

## 🎨 UI/UX Features

### Dark Theme Design
- **Monaco Editor Inspiration**: Clean, professional coding aesthetic
- **Bootstrap Integration**: Responsive design with consistent spacing
- **Feather Icons**: Lightweight, beautiful icon set
- **Chat Bubbles**: Distinct styling for user, assistant, and system messages

### Rich Text Support
- **Markdown-Style Formatting**: Bold, italic, code blocks
- **List Rendering**: Automatic bullet points and numbered lists
- **Paragraph Breaks**: Proper text spacing and readability
- **Loading Indicators**: Real-time feedback during API calls

## 🧪 Testing & Validation

### Conversation Memory Tests
1. Ask about a specific car model
2. Follow up with "How reliable is it?" (should reference the car)
3. Ask "What about maintenance costs?" (should maintain context)

### Content Filtering Tests
1. Ask about cooking → Should redirect to automotive topics
2. Ask about weather → Should politely decline and suggest car questions
3. Mix automotive terms with off-topic content → Should process automotive parts

### Security Tests
1. Check that API keys are never visible in browser dev tools
2. Verify session isolation between different browser tabs
3. Test error recovery when API calls fail

## 📝 Future Enhancement Ideas

### Immediate Improvements
- Add conversation export/import functionality
- Implement conversation search within history
- Add support for uploading car manuals (RAG integration)
- Include automotive image recognition

### Advanced Features
- Multi-language automotive support
- Voice input/output for hands-free interaction
- Integration with automotive databases (VIN lookup, recall info)
- Car recommendation engine based on user preferences

## 🤝 Contributing

When contributing to this project:

1. **Maintain Automotive Focus**: All features should serve automotive use cases
2. **Security First**: Never expose API keys or sensitive session data
3. **Conversation Context**: Preserve the conversation memory architecture
4. **User Experience**: Maintain the clean, professional interface design
5. **Error Handling**: Implement graceful failure recovery

## 📄 License

This project is designed for educational and personal use. Please respect OpenRouter's terms of service and API usage guidelines.

---

**Built with ❤️ for automotive enthusiasts and AI innovation**