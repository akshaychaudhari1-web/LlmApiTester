// Global variables
let currentApiKey = '';
let currentModel = 'deepseek/deepseek-chat-v3-0324:free';

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load session data on startup
    loadSessionData();
    
    // Test API Button
    const testApiBtn = document.getElementById('testApiBtn');
    if (testApiBtn) {
        testApiBtn.addEventListener('click', testOpenRouterAPI);
    }
    
    // Save Settings Button
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    
    // Chat functionality
    const sendChatBtn = document.getElementById('sendChatBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const chatInput = document.getElementById('chatInput');
    
    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', sendChatMessage);
    }
    
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', clearChat);
    }
    
    // Enter key in chat input
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});

// Load session data
async function loadSessionData() {
    try {
        const response = await fetch('/get_session_data');
        const data = await response.json();
        
        currentApiKey = data.api_key || '';
        currentModel = data.model || 'deepseek/deepseek-chat-v3-0324:free';
        
        // Update UI
        document.getElementById('apiKeyInput').value = currentApiKey;
        document.getElementById('modelSelect').value = currentModel;
    } catch (error) {
        console.error('Failed to load session data:', error);
    }
}

// Test OpenRouter API
async function testOpenRouterAPI() {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) {
        console.error('Chat input element not found');
        return;
    }
    
    const prompt = chatInput.value;
    const button = document.getElementById('testApiBtn');
    
    if (!currentApiKey) {
        addChatMessage('error', 'Please set your OpenRouter API key in Settings first');
        return;
    }
    
    if (!prompt.trim()) {
        addChatMessage('error', 'Please enter a prompt to test the API');
        return;
    }
    
    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    button.innerHTML = '<i data-feather="loader" class="me-1"></i>Calling API...';
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Add test message to chat
    addChatMessage('user', `[API TEST] ${prompt}`);
    const thinkingId = addChatMessage('assistant', 'Testing API connection...', true);
    
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
        
        // Remove thinking indicator
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }
        
        if (result.success) {
            addChatMessage('assistant', result.response.content);
            addChatMessage('system', `✓ API Test Successful • Model: ${result.model} • Usage: ${JSON.stringify(result.response.usage)}`);
        } else {
            addChatMessage('error', `API Test Failed: ${result.error}`);
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
        button.innerHTML = '<i data-feather="cloud" class="me-1"></i>API Test';
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Clear input
        chatInput.value = '';
    }
}

// Send chat message
async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendChatBtn');
    
    if (!chatInput || !sendBtn) {
        console.error('Chat elements not found');
        return;
    }
    
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    if (!currentApiKey) {
        addChatMessage('error', 'Please configure your OpenRouter API key in Settings first');
        return;
    }
    
    // Show loading state
    sendBtn.classList.add('loading');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i data-feather="loader" class="me-1"></i>Sending...';
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    
    // Add thinking indicator
    const thinkingId = addChatMessage('assistant', 'Thinking...', true);
    
    // Clear input
    chatInput.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const result = await response.json();
        
        // Remove thinking indicator
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) {
            thinkingElement.remove();
        }
        
        if (result.success) {
            addChatMessage('assistant', result.response.content);
        } else {
            addChatMessage('error', result.error || 'Failed to get response');
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
        sendBtn.classList.remove('loading');
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i data-feather="send" class="me-1"></i>Send';
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Add message to chat
function addChatMessage(type, content, isThinking = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.text-muted.text-center');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `message ${type} mb-3`;
    
    let iconClass = 'user';
    let bgClass = 'bg-primary';
    let textClass = 'text-white';
    
    switch (type) {
        case 'assistant':
            iconClass = 'message-circle';
            bgClass = 'bg-secondary';
            break;
        case 'error':
            iconClass = 'alert-circle';
            bgClass = 'bg-danger';
            break;
        case 'system':
            iconClass = 'info';
            bgClass = 'bg-success';
            break;
    }
    
    const thinkingClass = isThinking ? ' thinking' : '';
    
    messageDiv.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="flex-shrink-0 me-2">
                <div class="rounded-circle ${bgClass} ${textClass} p-2 d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                    <i data-feather="${iconClass}" style="width: 16px; height: 16px;"></i>
                </div>
            </div>
            <div class="flex-grow-1">
                <div class="bg-dark p-3 rounded${thinkingClass}" style="word-wrap: break-word;">
                    ${isThinking ? '<div class="typing-indicator"><span></span><span></span><span></span></div>' : content}
                </div>
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Replace feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    return messageId;
}

// Clear chat
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="text-muted text-center py-5">
            <i data-feather="message-circle" class="me-2" style="width: 48px; height: 48px;"></i>
            <h4>Welcome to OpenRouter Chat</h4>
            <p>Start a conversation with AI models through OpenRouter.<br>
            Configure your API key in Settings to get started.</p>
        </div>
    `;
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Save settings
async function saveSettings() {
    const apiKeyInput = document.getElementById('apiKeyInput');
    const modelSelect = document.getElementById('modelSelect');
    const saveBtn = document.getElementById('saveSettingsBtn');
    
    if (!apiKeyInput || !modelSelect) {
        console.error('Settings elements not found');
        return;
    }
    
    const apiKey = apiKeyInput.value.trim();
    const model = modelSelect.value;
    
    if (!apiKey) {
        alert('Please enter your OpenRouter API key');
        return;
    }
    
    // Show loading state
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        const response = await fetch('/test_openrouter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: apiKey,
                model: model,
                prompt: 'Hello, this is a test connection.'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update global variables
            currentApiKey = apiKey;
            currentModel = model;
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
            if (modal) {
                modal.hide();
            }
            
            // Show success message in chat
            addChatMessage('system', '✓ Settings saved successfully! OpenRouter connection verified.');
            
            console.log('Settings saved');
        } else {
            alert('Failed to verify API key: ' + result.error);
        }
    } catch (error) {
        alert('Failed to save settings: ' + error.message);
    } finally {
        // Reset button state
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Settings';
    }
}