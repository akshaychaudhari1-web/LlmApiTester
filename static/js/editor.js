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
    
    // Test API Button
    document.getElementById('testApiBtn').addEventListener('click', testOpenRouterAPI);
    
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
