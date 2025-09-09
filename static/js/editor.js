// Global variables
let editor;
let currentApiKey = '';
let currentModel = 'openai/gpt-3.5-turbo';

// Initialize Monaco Editor
require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.44.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
    // Create the editor
    editor = monaco.editor.create(document.getElementById('editor'), {
        value: `# Welcome to Python IDE for OpenRouter!
# You can write and execute Python code here, and test OpenRouter APIs

import requests
import json
import os

# Example: Simple OpenRouter API call
def test_openrouter():
    api_key = "your-api-key-here"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello! Write a simple Python function."}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error: {str(e)}"

# Uncomment the line below to test (make sure to add your API key)
# print(test_openrouter())

print("Welcome to the Python IDE for OpenRouter!")
print("Use the settings modal to configure your API key and model.")
`,
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        folding: true,
        wordWrap: 'on'
    });
    
    // Load session data on startup
    loadSessionData();
});

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Run Code Button
    document.getElementById('runCodeBtn').addEventListener('click', runCode);
    
    // Save Code Button
    document.getElementById('saveCodeBtn').addEventListener('click', showSaveSnippetModal);
    
    // Clear Code Button
    document.getElementById('clearCodeBtn').addEventListener('click', clearCode);
    
    // Clear Output Button
    document.getElementById('clearOutputBtn').addEventListener('click', clearOutput);
    
    // Test API Button (now in chat section)
    const testApiBtn = document.getElementById('testApiBtn');
    if (testApiBtn) {
        testApiBtn.addEventListener('click', testOpenRouterAPI);
    }
    
    // Save Settings Button
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    
    // Confirm Save Snippet Button
    document.getElementById('confirmSaveSnippetBtn').addEventListener('click', saveSnippet);
    
    // Load snippets when modal is opened
    document.getElementById('snippetsModal').addEventListener('show.bs.modal', loadSnippets);
    
    // Enter key in prompt input
    document.getElementById('promptInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            testOpenRouterAPI();
        }
    });
    
    // Enter key in snippet name input
    document.getElementById('snippetNameInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveSnippet();
        }
    });
    
    // Chat functionality
    document.getElementById('sendChatBtn').addEventListener('click', sendChatMessage);
    document.getElementById('clearChatBtn').addEventListener('click', clearChat);
    
    // Enter key in chat input
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
});

// Load session data
async function loadSessionData() {
    try {
        const response = await fetch('/get_session_data');
        const data = await response.json();
        
        currentApiKey = data.api_key || '';
        currentModel = data.model || 'openai/gpt-3.5-turbo';
        
        // Update UI
        document.getElementById('apiKeyInput').value = currentApiKey;
        document.getElementById('modelSelect').value = currentModel;
    } catch (error) {
        console.error('Failed to load session data:', error);
    }
}

// Run Python code
async function runCode() {
    const code = editor.getValue();
    const button = document.getElementById('runCodeBtn');
    const output = document.getElementById('consoleOutput');
    
    if (!code.trim()) {
        output.textContent = 'Error: No code to execute';
        return;
    }
    
    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    button.innerHTML = '<i data-feather="loader" class="me-1"></i>Running...';
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    output.textContent = 'Executing code...\n';
    
    try {
        const response = await fetch('/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code })
        });
        
        const result = await response.json();
        
        if (result.success) {
            let outputText = '';
            
            if (result.output) {
                outputText += `Output:\n${result.output}\n`;
            }
            
            if (result.error) {
                outputText += `Errors:\n${result.error}\n`;
            }
            
            outputText += `\nExecution completed in ${result.execution_time}s`;
            
            output.textContent = outputText || 'Code executed successfully with no output.';
        } else {
            output.textContent = `Error: ${result.error}`;
        }
    } catch (error) {
        output.textContent = `Network error: ${error.message}`;
    } finally {
        // Reset button state
        button.classList.remove('loading');
        button.disabled = false;
        button.innerHTML = '<i data-feather="play" class="me-1"></i>Run Code';
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Test OpenRouter API
async function testOpenRouterAPI() {
    const prompt = document.getElementById('promptInput').value;
    const button = document.getElementById('testApiBtn');
    const responseDiv = document.getElementById('apiResponse');
    
    if (!currentApiKey) {
        responseDiv.innerHTML = '<span class="text-danger">Error: Please set your OpenRouter API key in Settings</span>';
        return;
    }
    
    if (!prompt.trim()) {
        responseDiv.innerHTML = '<span class="text-danger">Error: Please enter a prompt</span>';
        return;
    }
    
    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    button.innerHTML = '<i data-feather="loader" class="me-1"></i>Calling API...';
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    responseDiv.innerHTML = '<em class="text-muted">Calling OpenRouter API...</em>';
    
    try {
        const response = await fetch('/test_openrouter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: currentApiKey,
                model: currentModel,
                prompt: prompt
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const formattedResponse = `Model: ${result.model}

Response:
${result.response.content}

Usage:
${JSON.stringify(result.response.usage, null, 2)}`;
            
            responseDiv.textContent = formattedResponse;
        } else {
            responseDiv.innerHTML = `<span class="text-danger">Error: ${result.error}</span>`;
        }
    } catch (error) {
        responseDiv.innerHTML = `<span class="text-danger">Network error: ${error.message}</span>`;
    } finally {
        // Reset button state
        button.classList.remove('loading');
        button.disabled = false;
        button.innerHTML = '<i data-feather="send" class="me-1"></i>Test API';
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Save settings
function saveSettings() {
    currentApiKey = document.getElementById('apiKeyInput').value;
    currentModel = document.getElementById('modelSelect').value;
    
    // Close modal
    if (typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        if (modal) modal.hide();
    }
    
    // Show success message (you could add a toast here)
    console.log('Settings saved');
}

// Clear code editor
function clearCode() {
    if (confirm('Are you sure you want to clear the code editor?')) {
        editor.setValue('');
    }
}

// Clear output
function clearOutput() {
    document.getElementById('consoleOutput').textContent = '';
}

// Show save snippet modal
function showSaveSnippetModal() {
    const code = editor.getValue();
    if (!code.trim()) {
        alert('No code to save');
        return;
    }
    
    document.getElementById('snippetNameInput').value = '';
    if (typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(document.getElementById('saveSnippetModal'));
        modal.show();
    }
}

// Save snippet
async function saveSnippet() {
    const name = document.getElementById('snippetNameInput').value;
    const code = editor.getValue();
    
    if (!name.trim()) {
        alert('Please enter a name for the snippet');
        return;
    }
    
    if (!code.trim()) {
        alert('No code to save');
        return;
    }
    
    try {
        const response = await fetch('/save_snippet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                code: code
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal
            if (typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(document.getElementById('saveSnippetModal'));
                if (modal) modal.hide();
            }
            
            alert('Snippet saved successfully!');
        } else {
            alert(`Error saving snippet: ${result.error}`);
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
    }
}

// Load snippets
async function loadSnippets() {
    const snippetsList = document.getElementById('snippetsList');
    snippetsList.innerHTML = '<div class="text-center"><em class="text-muted">Loading snippets...</em></div>';
    
    try {
        const response = await fetch('/load_snippets');
        const result = await response.json();
        
        if (result.success) {
            if (result.snippets.length === 0) {
                snippetsList.innerHTML = '<div class="text-center"><em class="text-muted">No saved snippets</em></div>';
                return;
            }
            
            snippetsList.innerHTML = '';
            
            result.snippets.forEach(snippet => {
                const snippetItem = document.createElement('div');
                snippetItem.className = 'list-group-item d-flex justify-content-between align-items-start';
                snippetItem.innerHTML = `
                    <div class="ms-2 me-auto">
                        <div class="fw-bold">${escapeHtml(snippet.name)}</div>
                        <div class="snippet-meta">
                            Created: ${new Date(snippet.created_at).toLocaleDateString()}
                            ${snippet.updated_at !== snippet.created_at ? '• Updated: ' + new Date(snippet.updated_at).toLocaleDateString() : ''}
                        </div>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="loadSnippet(${snippet.id})">
                            <i data-feather="eye" width="16" height="16"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteSnippet(${snippet.id})">
                            <i data-feather="trash-2" width="16" height="16"></i>
                        </button>
                    </div>
                `;
                snippetsList.appendChild(snippetItem);
            });
            
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        } else {
            snippetsList.innerHTML = `<div class="text-center text-danger">Error: ${result.error}</div>`;
        }
    } catch (error) {
        snippetsList.innerHTML = `<div class="text-center text-danger">Network error: ${error.message}</div>`;
    }
}

// Load specific snippet
async function loadSnippet(snippetId) {
    try {
        const response = await fetch(`/load_snippet/${snippetId}`);
        const result = await response.json();
        
        if (result.success) {
            editor.setValue(result.snippet.code);
            
            // Close modal
            if (typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(document.getElementById('snippetsModal'));
                if (modal) modal.hide();
            }
        } else {
            alert(`Error loading snippet: ${result.error}`);
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
    }
}

// Delete snippet
async function deleteSnippet(snippetId) {
    if (!confirm('Are you sure you want to delete this snippet?')) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_snippet/${snippetId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            loadSnippets(); // Reload the list
        } else {
            alert(`Error deleting snippet: ${result.error}`);
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
    }
}

// Chat functionality
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    const button = document.getElementById('sendChatBtn');
    const messagesContainer = document.getElementById('chatMessages');
    
    if (!message) {
        return;
    }
    
    // Clear the welcome message if it exists
    const welcomeMsg = messagesContainer.querySelector('.text-muted.text-center');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';
    
    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    button.innerHTML = '<i data-feather="loader" class="me-1"></i>Thinking...';
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Add thinking indicator
    const thinkingId = addChatMessage('assistant', 'Thinking about your automotive question...', true);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const result = await response.json();
        
        // Remove thinking indicator
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }
        
        if (result.success) {
            const responseContent = result.response.content;
            addChatMessage('assistant', responseContent);
            
            // Show model info if available
            if (result.response.model && !result.response.filtered) {
                addChatMessage('system', `Response generated by: ${result.response.model}`);
            }
        } else {
            addChatMessage('error', `Error: ${result.error}`);
        }
    } catch (error) {
        // Remove thinking indicator
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }
        addChatMessage('error', `Network error: ${error.message}`);
    } finally {
        // Reset button state
        button.classList.remove('loading');
        button.disabled = false;
        button.innerHTML = '<i data-feather="send" class="me-1"></i>Send';
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

function addChatMessage(type, content, isTemporary = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = 'mb-3';
    
    let iconClass, bgClass, textClass;
    
    switch (type) {
        case 'user':
            iconClass = 'user';
            bgClass = 'bg-primary';
            textClass = 'text-white';
            break;
        case 'assistant':
            iconClass = 'message-circle';
            bgClass = isTemporary ? 'bg-secondary' : 'bg-success';
            textClass = 'text-white';
            break;
        case 'error':
            iconClass = 'alert-circle';
            bgClass = 'bg-danger';
            textClass = 'text-white';
            break;
        case 'system':
            iconClass = 'info';
            bgClass = 'bg-info';
            textClass = 'text-white';
            break;
        default:
            iconClass = 'message-square';
            bgClass = 'bg-secondary';
            textClass = 'text-white';
    }
    
    messageDiv.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="${bgClass} ${textClass} rounded-circle p-2 me-3" style="min-width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                <i data-feather="${iconClass}" width="18" height="18"></i>
            </div>
            <div class="flex-grow-1">
                <div class="bg-dark text-light p-3 rounded">
                    <div class="message-content">${escapeHtml(content)}</div>
                    <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    return messageId;
}

async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        const response = await fetch('/clear_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = `
                <div class="text-muted text-center py-4">
                    <i data-feather="car" class="me-2"></i>
                    Ask me anything about automobiles, cars, or automotive technology!
                    <br><small>Topics are filtered to automotive discussions only.</small>
                </div>
            `;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        } else {
            alert(`Error clearing chat: ${result.error}`);
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
