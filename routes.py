import json
import logging
import uuid
from flask import render_template, request, jsonify, session
from app import app
from openrouter_client import OpenRouterClient
import re

# Server-side storage for secure data (API keys and chat history)
# This prevents sensitive data from being stored in client cookies
secure_sessions = {}

@app.route('/')
def index():
    """Chat assistant interface"""
    return render_template('index.html')


def get_or_create_secure_session_id():
    """Get or create a secure session ID for server-side storage"""
    if 'secure_session_id' not in session:
        session['secure_session_id'] = str(uuid.uuid4())
    return session['secure_session_id']

def get_secure_session_data(session_id):
    """Get secure session data from server-side storage"""
    if session_id not in secure_sessions:
        secure_sessions[session_id] = {
            'api_key': '',
            'model': 'deepseek/deepseek-chat-v3-0324:free',
            'chat_history': []
        }
    return secure_sessions[session_id]

@app.route('/test_openrouter', methods=['POST'])
def test_openrouter():
    """Test OpenRouter API connection"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')  # Frontend can still set API key
        model = data.get('model', 'openai/gpt-3.5-turbo')
        prompt = data.get('prompt', 'Hello, world!')
        
        # Get secure session data 
        session_id = get_or_create_secure_session_id()
        secure_data = get_secure_session_data(session_id)
        
        # Use provided API key or fallback to stored one
        if api_key:
            # Frontend provided new API key - store it
            secure_data['api_key'] = api_key
            secure_data['model'] = model
        else:
            # Use stored API key for testing
            api_key = secure_data['api_key']
            secure_data['model'] = model
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'})
        
        client = OpenRouterClient(api_key)
        # For API testing, create a simple conversation history with just the test prompt
        test_conversation = [
            {
                'role': 'user',
                'content': prompt
            }
        ]
        response = client.chat_completion(model, test_conversation)
        
        return jsonify({
            'success': True,
            'response': response,
            'model': model
        })
    
    except Exception as e:
        logging.error(f"OpenRouter API error: {str(e)}")
        return jsonify({'success': False, 'error': f'API call failed: {str(e)}'})





@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    """Get stored session data (secure - no API key exposure)"""
    session_id = get_or_create_secure_session_id()
    secure_data = get_secure_session_data(session_id)
    
    return jsonify({
        'api_key': '***' if secure_data['api_key'] else '',  # Never expose actual API key
        'model': secure_data['model'],
        'has_api_key': bool(secure_data['api_key'])  # Just indicate if key is set
    })

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear all session data"""
    # Clear server-side secure data
    session_id = session.get('secure_session_id')
    if session_id and session_id in secure_sessions:
        del secure_sessions[session_id]
    
    # Clear client-side session
    session.clear()
    return jsonify({'success': True, 'message': 'Session data cleared'})

# Automotive topic keywords for filtering
AUTOMOTIVE_KEYWORDS = [
    # Automotive terms
    'car', 'cars', 'vehicle', 'vehicles', 'auto', 'automobile', 'automotive',
    'engine', 'motor', 'transmission', 'brake', 'brakes', 'tire', 'tires',
    'wheel', 'wheels', 'suspension', 'chassis', 'frame', 'body', 'paint',
    'fuel', 'gasoline', 'diesel', 'electric', 'hybrid', 'battery', 'charging',
    'horsepower', 'torque', 'performance', 'speed', 'acceleration', 'handling',
    'safety', 'airbag', 'seatbelt', 'crash', 'collision', 'insurance',
    'maintenance', 'repair', 'service', 'oil', 'filter', 'spark', 'plug',
    'toyota', 'honda', 'ford', 'gm', 'chevrolet', 'nissan', 'bmw', 'mercedes',
    'audi', 'volkswagen', 'porsche', 'ferrari', 'lamborghini', 'tesla',
    'suv', 'sedan', 'coupe', 'hatchback', 'truck', 'pickup', 'van', 'minivan',
    'roadster', 'convertible', 'wagon', 'crossover', 'sports car', 'luxury',
    'racing', 'formula', 'nascar', 'drift', 'track', 'circuit', 'rally',
    
    # Conversational keywords
    'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
    'thanks', 'thank you', 'please', 'sure', 'ok', 'okay', 'yes', 'no',
    'next', 'continue', 'more', 'again', 'repeat', 'explain', 'clarify',
    'i dont understand', 'i didnt understand', 'confused', 'help', 'sorry',
    'what', 'how', 'when', 'where', 'why', 'who', 'which', 'can you',
    'tell me', 'show me', 'explain to me', 'i want', 'i need', 'i would like',
    'exit', 'quit', 'bye', 'goodbye', 'see you', 'stop', 'end', 'finish',
    
    # Casual conversational words
    'hmm', 'hm', 'uh', 'um', 'eh', 'ah', 'oh', 'wow', 'woah', 'whoa',
    'yep', 'yup', 'nope', 'nah', 'maybe', 'perhaps', 'probably', 'definitely',
    'absolutely', 'exactly', 'right', 'correct', 'true', 'precisely',
    'awesome', 'cool', 'nice', 'great', 'amazing', 'fantastic', 'wonderful',
    'interesting', 'really', 'seriously', 'actually', 'basically', 'essentially',
    'huh', 'excuse me', 'pardon', 'come again', 'what?', 'huh?',
    'sup', 'whats up', 'howdy', 'yo', 'hey there', 'hi there',
    'so', 'well', 'anyway', 'actually', 'basically', 'essentially',
    'later', 'catch you later', 'talk soon', 'peace out', 'see ya',
    'lol', 'haha', 'funny', 'sad', 'happy', 'excited', 'good job', 'well done',
    'let me think', 'give me a sec', 'hold on', 'wait', 'one moment',
    'sweet', 'dope', 'sick', 'tight', 'rad', 'legit', 'bet', 'word',
    'got it', 'makes sense', 'i see', 'fair enough', 'sounds good',
    'no way', 'for real', 'no kidding', 'you bet', 'of course',
    'my bad', 'no worries', 'all good', 'no problem', 'dont worry about it'
]

def is_automotive_related(text):
    """Check if the text is related to automotive topics"""
    text_lower = text.lower()
    # Check for automotive keywords
    for keyword in AUTOMOTIVE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

@app.route('/chat', methods=['POST'])
def chat():
    """Handle automotive chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Get secure session data
        session_id = get_or_create_secure_session_id()
        secure_data = get_secure_session_data(session_id)
        
        # Check if user has API key configured
        api_key = secure_data['api_key']
        if not api_key:
            return jsonify({
                'success': False, 
                'error': 'Please configure your OpenRouter API key in Settings first'
            })
        
        # Content filtering - check if message is automotive related
        if not is_automotive_related(message):
            return jsonify({
                'success': True,
                'response': {
                    'content': "I'm sorry, but I can only discuss automotive topics like cars, engines, vehicle maintenance, auto manufacturers, and automotive technology. Please ask me something related to automobiles!",
                    'filtered': True
                }
            })
        
        # Get model and conversation history from secure storage
        model = secure_data['model']
        conversation_history = secure_data['chat_history']
        
        # Add user message to conversation history
        conversation_history.append({
            'role': 'user',
            'content': message
        })
        
        # Limit conversation history to last 10 messages to avoid token limits
        # Keep system message separate, so we track user/assistant pairs
        if len(conversation_history) > 20:  # 20 = 10 user + 10 assistant messages
            conversation_history = conversation_history[-20:]
        
        # Call OpenRouter API with conversation history
        client = OpenRouterClient(api_key)
        try:
            response = client.chat_completion(model, conversation_history)
            
            # Add assistant response to conversation history
            conversation_history.append({
                'role': 'assistant',
                'content': response['content']
            })
            
            # Update secure storage with new conversation history
            secure_data['chat_history'] = conversation_history
            
            return jsonify({
                'success': True,
                'response': {
                    'content': response['content'],
                    'model': response.get('model', model),
                    'filtered': False
            }
            })
        except Exception as api_error:
            logging.error(f"OpenRouter API timeout/error: {str(api_error)}")
            
            # Remove the user message from history if API call failed
            if conversation_history and conversation_history[-1]['role'] == 'user':
                conversation_history.pop()
                secure_data['chat_history'] = conversation_history
            
            return jsonify({
                'success': True,
                'response': {
                    'content': "I'm sorry, but I'm having trouble connecting to the AI service right now. This might be due to high traffic or a temporary issue. Please try again in a moment!",
                    'model': model,
                    'filtered': False
            }
            })
    
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'error': f'Chat failed: {str(e)}'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear chat history from secure storage"""
    session_id = get_or_create_secure_session_id()
    secure_data = get_secure_session_data(session_id)
    secure_data['chat_history'] = []
    return jsonify({'success': True, 'message': 'Chat history cleared'})
