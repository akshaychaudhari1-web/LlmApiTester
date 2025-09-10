import os
import uuid
import logging
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, DocumentChunk, ChatHistory
from document_processor import DocumentProcessor, VectorSearchEngine
from rag_client import RAGClient

logger = logging.getLogger(__name__)

# In-memory storage for session data (similar to automotive chat)
secure_sessions = {}

# Initialize components
document_processor = DocumentProcessor()
vector_search = None  # Will be initialized in first request

ALLOWED_EXTENSIONS = {'pdf'}
AUTOMOTIVE_KEYWORDS = [
    'car', 'automobile', 'vehicle', 'engine', 'motor', 'transmission', 'brake',
    'suspension', 'steering', 'tire', 'wheel', 'battery', 'fuel', 'oil', 
    'maintenance', 'repair', 'diagnostic', 'performance', 'safety', 'airbag',
    'toyota', 'honda', 'ford', 'chevrolet', 'bmw', 'mercedes', 'audi',
    'what', 'how', 'when', 'where', 'why', 'tell', 'explain', 'help',
    'hi', 'hello', 'thanks', 'please'
]

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_or_create_secure_session_id():
    """Get or create secure session ID"""
    if 'secure_session_id' not in session:
        session['secure_session_id'] = str(uuid.uuid4())
    return session['secure_session_id']

def get_secure_session_data(session_id):
    """Get secure session data"""
    if session_id not in secure_sessions:
        secure_sessions[session_id] = {
            'api_key': '',
            'model': 'openrouter/sonoma-sky-alpha',
            'chat_history': []
        }
    return secure_sessions[session_id]

def get_vector_search():
    """Get or initialize vector search engine"""
    global vector_search
    if vector_search is None:
        vector_search = VectorSearchEngine()
    return vector_search

def is_automotive_related(text):
    """Check if text contains automotive keywords"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in AUTOMOTIVE_KEYWORDS)

@app.route('/')
def index():
    """Main page with chat interface and document management"""
    return render_template('index.html')

@app.route('/upload_document', methods=['POST'])
def upload_document():
    """Upload and process PDF document"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'})
        
        # Check file size (16MB limit)
        if request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large (max 16MB)'})
        
        # Generate secure filename
        original_filename = file.filename or "unknown.pdf"
        filename = secure_filename(f"{uuid.uuid4()}_{original_filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(file_path)
        
        # Process document
        document = document_processor.process_pdf(file_path, filename, original_filename)
        
        # Refresh search index
        get_vector_search().refresh_index()
        
        return jsonify({
            'success': True,
            'message': f'Document "{original_filename}" uploaded and processed successfully',
            'document': document.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        documents = Document.query.all()
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents]
        })
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_document/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document and its chunks"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database (chunks will be deleted due to cascade)
        db.session.delete(document)
        db.session.commit()
        
        # Refresh search index
        get_vector_search().refresh_index()
        
        return jsonify({
            'success': True,
            'message': f'Document "{document.original_filename}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """RAG-powered chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Check if automotive-related
        if not is_automotive_related(message):
            return jsonify({
                'success': True,
                'response': {
                    'content': "I'm an automotive expert assistant. I can only help with questions about cars, engines, maintenance, and other automotive topics. Please ask me something about vehicles!",
                    'model': 'content_filter',
                    'filtered': True,
                    'context_used': False,
                    'chunks_found': 0,
                    'referenced_documents': []
                }
            })
        
        # Get session data
        session_id = get_or_create_secure_session_id()
        secure_data = get_secure_session_data(session_id)
        
        if not secure_data['api_key']:
            return jsonify({'success': False, 'error': 'Please configure your OpenRouter API key in settings'})
        
        # Initialize RAG client
        rag_client = RAGClient(secure_data['api_key'])
        
        # Get conversation history
        conversation_history = secure_data['chat_history']
        
        # Add user message to history
        conversation_history.append({'role': 'user', 'content': message})
        
        # Truncate conversation if too long
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Generate RAG response
        response = rag_client.chat_with_rag(
            message=message,
            conversation_history=conversation_history,
            model=secure_data['model']
        )
        
        if response['success']:
            # Add assistant response to history
            assistant_message = response['response']['content']
            conversation_history.append({'role': 'assistant', 'content': assistant_message})
            
            # Update session
            secure_data['chat_history'] = conversation_history
            
            # Store in database for persistence
            user_chat = ChatHistory()
            user_chat.session_id = session_id
            user_chat.role = 'user'
            user_chat.content = message
            
            assistant_chat = ChatHistory()
            assistant_chat.session_id = session_id
            assistant_chat.role = 'assistant'
            assistant_chat.content = assistant_message
            
            # Set referenced documents
            if response['response']['referenced_documents']:
                doc_ids = [doc['id'] for doc in response['response']['referenced_documents']]
                assistant_chat.set_referenced_documents(doc_ids)
            
            db.session.add(user_chat)
            db.session.add(assistant_chat)
            db.session.commit()
            
            return jsonify(response)
        else:
            # Remove user message on failure
            if conversation_history and conversation_history[-1]['role'] == 'user':
                conversation_history.pop()
            secure_data['chat_history'] = conversation_history
            
            return jsonify(response)
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_openrouter', methods=['POST'])
def test_openrouter():
    """Test OpenRouter API connection"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        model = data.get('model', 'openrouter/sonoma-sky-alpha')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'})
        
        # Test connection
        rag_client = RAGClient(api_key)
        result = rag_client.test_connection(api_key, model)
        
        if result['success']:
            # Store API key in session
            session_id = get_or_create_secure_session_id()
            secure_data = get_secure_session_data(session_id)
            secure_data['api_key'] = api_key
            secure_data['model'] = model
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API test error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    """Get session configuration data (masked)"""
    try:
        session_id = get_or_create_secure_session_id()
        secure_data = get_secure_session_data(session_id)
        
        return jsonify({
            'api_key': '***' if secure_data['api_key'] else '',
            'model': secure_data['model'],
            'has_api_key': bool(secure_data['api_key']),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Session data error: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear all session data"""
    try:
        session_id = session.get('secure_session_id')
        if session_id and session_id in secure_sessions:
            del secure_sessions[session_id]
        session.clear()
        
        return jsonify({'success': True, 'message': 'Session cleared'})
        
    except Exception as e:
        logger.error(f"Clear session error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear chat history only"""
    try:
        session_id = get_or_create_secure_session_id()
        secure_data = get_secure_session_data(session_id)
        secure_data['chat_history'] = []
        
        return jsonify({'success': True, 'message': 'Chat history cleared'})
        
    except Exception as e:
        logger.error(f"Clear chat error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        rag_client = RAGClient()
        stats = rag_client.get_document_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/refresh_index', methods=['POST'])
def refresh_index():
    """Manually refresh the search index"""
    try:
        get_vector_search().refresh_index()
        return jsonify({'success': True, 'message': 'Search index refreshed'})
        
    except Exception as e:
        logger.error(f"Refresh index error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})