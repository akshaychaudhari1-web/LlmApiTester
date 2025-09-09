import json
import logging
from flask import render_template, request, jsonify, session
from app import app, db
from models import CodeSnippet
from code_executor import execute_python_code
from openrouter_client import OpenRouterClient

@app.route('/')
def index():
    """Main IDE interface"""
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_code():
    """Execute Python code and return results"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code.strip():
            return jsonify({'success': False, 'error': 'No code provided'})
        
        # Execute the code
        result = execute_python_code(code)
        
        return jsonify({
            'success': True,
            'output': result['output'],
            'error': result['error'],
            'execution_time': result['execution_time']
        })
    
    except Exception as e:
        logging.error(f"Code execution error: {str(e)}")
        return jsonify({'success': False, 'error': f'Execution failed: {str(e)}'})

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

@app.route('/save_snippet', methods=['POST'])
def save_snippet():
    """Save a code snippet"""
    try:
        data = request.get_json()
        name = data.get('name', '')
        code = data.get('code', '')
        
        if not name or not code:
            return jsonify({'success': False, 'error': 'Name and code are required'})
        
        snippet = CodeSnippet(name=name, code=code)
        db.session.add(snippet)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'snippet': snippet.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Save snippet error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to save snippet: {str(e)}'})

@app.route('/load_snippets', methods=['GET'])
def load_snippets():
    """Load all saved code snippets"""
    try:
        snippets = CodeSnippet.query.order_by(CodeSnippet.updated_at.desc()).all()
        return jsonify({
            'success': True,
            'snippets': [snippet.to_dict() for snippet in snippets]
        })
    
    except Exception as e:
        logging.error(f"Load snippets error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to load snippets: {str(e)}'})

@app.route('/load_snippet/<int:snippet_id>', methods=['GET'])
def load_snippet(snippet_id):
    """Load a specific code snippet"""
    try:
        snippet = CodeSnippet.query.get_or_404(snippet_id)
        return jsonify({
            'success': True,
            'snippet': snippet.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Load snippet error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to load snippet: {str(e)}'})

@app.route('/delete_snippet/<int:snippet_id>', methods=['DELETE'])
def delete_snippet(snippet_id):
    """Delete a code snippet"""
    try:
        snippet = CodeSnippet.query.get_or_404(snippet_id)
        db.session.delete(snippet)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        logging.error(f"Delete snippet error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to delete snippet: {str(e)}'})

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    """Get stored session data"""
    return jsonify({
        'api_key': session.get('openrouter_api_key', ''),
        'model': session.get('openrouter_model', 'openai/gpt-3.5-turbo')
    })
