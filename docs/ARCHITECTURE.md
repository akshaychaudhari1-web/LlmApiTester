# Technical Architecture

## System Overview

The Automotive Chat Assistant follows a traditional three-tier web architecture with enhanced security and conversation state management:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Browser)     │◄──►│   (Flask)       │◄──►│   (OpenRouter)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                      │                      │
│ • Chat Interface     │ • Session Management │ • AI Models
│ • Rich Text          │ • Content Filtering  │ • API Gateway
│ • API Calls          │ • Conversation State │ • Rate Limiting
│ • Local Storage      │ • Database ORM       │
└─────────────────     └─────────────────     └─────────────────
```

## File Structure & Responsibilities

### Core Application Files

#### `app.py` - Application Bootstrap
```python
# Primary responsibilities:
- Flask application initialization
- Database configuration (PostgreSQL)
- Environment variable validation
- Middleware setup (ProxyFix for deployment)
- Route registration
- Error handling setup
```

**Key Features:**
- Environment validation on startup
- Graceful error handling for database failures
- Production-ready configuration with proxy support
- Automatic table creation

#### `routes.py` - API Endpoints & Business Logic
```python
# Primary responsibilities:
- HTTP request handling
- Session management
- Conversation state management
- Content filtering logic
- OpenRouter API orchestration
- Error recovery mechanisms
```

**Endpoint Architecture:**
```
/                 → Chat interface (GET)
/chat             → Message processing (POST)
/test_openrouter  → API validation (POST)
/get_session_data → Session info retrieval (GET)
/clear_session    → Full session reset (POST)
/clear_chat       → Conversation reset (POST)
```

#### `openrouter_client.py` - AI Integration Layer
```python
# Primary responsibilities:
- OpenRouter API communication
- System prompt injection
- Request/response handling
- Error handling and retries
- Timeout management
- Header configuration
```

**API Integration Pattern:**
```python
system_prompt + conversation_history → OpenRouter → formatted_response
```

#### `models.py` - Data Layer
```python
# Primary responsibilities:
- Database schema definition
- ORM model classes
- Data serialization methods
- Relationship definitions
```

**Current Schema:**
- `CodeSnippet`: Legacy model from IDE version (minimal usage)
- Future: Conversation persistence, user management

### Frontend Architecture

#### `templates/index.html` - User Interface
```html
<!-- Structure -->
<nav>Settings & Controls</nav>
<main>
  <div>Chat Messages Container</div>
  <div>Input & Send Controls</div>
</main>
<modal>API Configuration</modal>
```

**Component Hierarchy:**
- Bootstrap 5 responsive layout
- Feather icons integration
- Modal-based settings
- Accessible form controls

#### `static/js/editor.js` - Client Logic
```javascript
// Core functions:
- loadSessionData()     // Retrieve masked session info
- sendChatMessage()     // Main chat functionality
- testOpenRouterAPI()   // API connection testing
- addChatMessage()      // UI message rendering
- formatTextContent()   // Rich text processing
- saveSettings()        // Configuration persistence
```

**Event Flow:**
```
User Input → Validation → API Call → Response Processing → UI Update
```

#### `static/css/custom.css` - Styling Layer
```css
/* Key components: */
- Dark theme variables
- Chat bubble styling
- Loading animations
- Responsive layout rules
- Accessibility enhancements
```

## Data Flow Architecture

### Session Management Flow
```
1. User visits site
   ↓
2. Generate secure_session_id (UUID)
   ↓
3. Store in Flask session cookie (signed, not encrypted)
   ↓
4. Create server-side storage: secure_sessions[uuid]
   ↓
5. All sensitive data stored server-side only
```

### Conversation Flow
```
1. User sends message
   ↓
2. Frontend validation (automotive keywords)
   ↓
3. Server-side filtering (content validation)
   ↓
4. Retrieve conversation history from secure storage
   ↓
5. Append user message to history
   ↓
6. Send full context to OpenRouter (system prompt + history)
   ↓
7. Process AI response
   ↓
8. Append AI response to history
   ↓
9. Update secure storage
   ↓
10. Return formatted response to frontend
```

### Error Recovery Flow
```
API Failure Detected
   ↓
Remove last user message from history
   ↓
Update secure storage (rollback)
   ↓
Return friendly error message
   ↓
Maintain conversation consistency
```

## Security Architecture

### Session Security Model
```python
# Client Side (Cookie)
session = {
    'secure_session_id': 'uuid-v4-string'  # Only identifier
}

# Server Side (Memory)
secure_sessions = {
    'uuid-v4-string': {
        'api_key': 'sk-actual-openrouter-key',
        'model': 'deepseek/deepseek-chat-v3-0324:free',
        'chat_history': [
            {'role': 'user', 'content': 'message'},
            {'role': 'assistant', 'content': 'response'}
        ]
    }
}
```

### Content Security Model
```python
# Layer 1: Frontend Keyword Filtering
AUTOMOTIVE_KEYWORDS = [
    'car', 'engine', 'brake', 'toyota', 'maintenance',
    'hi', 'hello', 'what', 'how'  # Conversational terms
]

# Layer 2: LLM System Prompt Enforcement
system_prompt = "You are an automotive expert assistant..."

# Layer 3: Response Validation (Future Enhancement)
# Could add post-response filtering if needed
```

## Database Architecture

### Current Schema
```sql
-- Legacy from IDE version
CREATE TABLE code_snippet (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Recommended Future Schema
```sql
-- For production conversation persistence
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message_role VARCHAR(10) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encrypted_key TEXT NOT NULL,
    model_preference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Integration Architecture

### OpenRouter Integration
```python
# Request Structure
{
    "model": "deepseek/deepseek-chat-v3-0324:free",
    "messages": [
        {"role": "system", "content": "automotive_system_prompt"},
        {"role": "user", "content": "user_message_1"},
        {"role": "assistant", "content": "ai_response_1"},
        {"role": "user", "content": "user_message_2"}
    ],
    "max_tokens": 1000,
    "temperature": 0.7
}

# Response Processing
response.choices[0].message.content → formatted_output
```

### Production Deployment
```
Internet → Reverse Proxy (Nginx) → Gunicorn Workers → Flask App
                                       ↓
                                  PostgreSQL Database
                                       ↓
                                  Redis Session Store (Recommended)
```

## Performance Considerations

### Memory Management
- **Current**: In-memory session storage (`secure_sessions` dict)
- **Limitation**: Memory growth, no persistence across restarts
- **Solution**: Migrate to Redis with TTL

### Conversation History Management
- **Current**: 20-message limit (10 user + 10 assistant)
- **Token Efficiency**: Prevents context window overflow
- **Enhancement**: Token-aware truncation vs simple message count

### API Optimization
- **Timeout Strategy**: 15s request timeout + graceful degradation
- **Rate Limiting**: Currently none (recommend Flask-Limiter)
- **Caching**: No response caching (stateful conversations)

## Scalability Architecture

### Current Limitations
1. **Single-Process Session Storage**: Won't work with multiple Gunicorn workers
2. **No Load Balancing**: Sessions tied to specific worker processes
3. **Memory Leaks**: No TTL or cleanup for abandoned sessions

### Recommended Scaling Pattern
```python
# Replace in-memory storage with Redis
import redis
from flask_session import Session

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'automotive_chat:'

Session(app)
```

### Multi-Worker Deployment
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 3
  redis:
    image: redis:alpine
  postgres:
    image: postgres:15
```

## Monitoring & Observability

### Current Logging
```python
logging.basicConfig(level=logging.DEBUG)
# Logs: API calls, errors, session events
```

### Recommended Monitoring
```python
# Add structured logging
import structlog

# Add metrics collection
from prometheus_client import Counter, Histogram

# Add health checks
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow()}
```

## Security Hardening Roadmap

### Immediate (Current Implementation)
- ✅ Server-side session storage
- ✅ No client-side secret exposure
- ✅ Input validation
- ✅ Error handling

### Short-term Recommendations
- 🔄 Add CSRF protection
- 🔄 Implement rate limiting
- 🔄 Add session TTL
- 🔄 Input sanitization

### Long-term Security
- 🔄 API key encryption at rest
- 🔄 Audit logging
- 🔄 User authentication (optional)
- 🔄 Content Security Policy headers