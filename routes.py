import json
import logging
from flask import render_template, request, jsonify, session
from app import app
from openrouter_client import OpenRouterClient
import re

@app.route('/')
def index():
    """Chat assistant interface"""
    return render_template('index.html')


@app.route('/test_openrouter', methods=['POST'])
def test_openrouter():
    """Test OpenRouter API connection"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        model = data.get('model', 'openai/gpt-3.5-turbo')
        prompt = data.get('prompt', 'Hello, world!')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'})
        
        # Store API key in session
        session['openrouter_api_key'] = api_key
        session['openrouter_model'] = model
        
        client = OpenRouterClient(api_key)
        response = client.chat_completion(model, prompt)
        
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
    """Get stored session data"""
    return jsonify({
        'api_key': session.get('openrouter_api_key', ''),
        'model': session.get('openrouter_model', 'deepseek/deepseek-chat-v3-0324:free')
    })

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear all session data"""
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
    'exit', 'quit', 'bye', 'goodbye', 'see you', 'stop', 'end', 'finish'
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
        
        # Check if user has API key configured
        api_key = session.get('openrouter_api_key')
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
        
        # Get model from session
        model = session.get('openrouter_model', 'deepseek/deepseek-chat-v3-0324:free')
        
        # Call OpenRouter API directly with user's message
        client = OpenRouterClient(api_key)
        response = client.chat_completion(model, message)
        
        return jsonify({
            'success': True,
            'response': {
                'content': response['content'],
                'model': response.get('model', model),
                'filtered': False
            }
        })
    
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'error': f'Chat failed: {str(e)}'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear chat history from session"""
    if 'chat_history' in session:
        del session['chat_history']
    return jsonify({'success': True, 'message': 'Chat history cleared'})
