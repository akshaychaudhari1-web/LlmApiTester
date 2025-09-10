// Pilot RAG - Frontend JavaScript

class PilotRAG {
    constructor() {
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSessionData();
        this.loadDocuments();
        this.refreshStats();
    }

    setupEventListeners() {
        // Enter key in message input
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // File upload
        document.getElementById('file-upload').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadDocument(e.target.files[0]);
            }
        });

        // Drag and drop for file upload
        this.setupDragAndDrop();

        // Settings form
        document.getElementById('settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });
    }

    setupDragAndDrop() {
        const uploadSection = document.querySelector('.upload-section');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadSection.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadSection.addEventListener(eventName, () => {
                uploadSection.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadSection.addEventListener(eventName, () => {
                uploadSection.classList.remove('dragover');
            });
        });

        uploadSection.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === 'application/pdf') {
                this.uploadDocument(files[0]);
            } else {
                this.showAlert('Please upload a PDF file', 'warning');
            }
        });
    }

    async loadSessionData() {
        try {
            const response = await fetch('/get_session_data');
            const data = await response.json();
            
            if (data.error) {
                console.error('Session data error:', data.error);
                return;
            }

            // Update settings form
            document.getElementById('api-key').placeholder = data.has_api_key ? 'API key configured' : 'Enter your OpenRouter API key';
            document.getElementById('model-select').value = data.model;
            
        } catch (error) {
            console.error('Error loading session data:', error);
        }
    }

    async loadDocuments() {
        try {
            const response = await fetch('/get_documents');
            const data = await response.json();
            
            if (data.success) {
                this.renderDocuments(data.documents);
            } else {
                console.error('Error loading documents:', data.error);
            }
        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }

    renderDocuments(documents) {
        const container = document.getElementById('documents-container');
        
        if (documents.length === 0) {
            container.innerHTML = `
                <div class="text-muted small">
                    <i data-feather="info"></i>
                    Upload automotive PDFs to get started
                </div>
            `;
        } else {
            container.innerHTML = documents.map(doc => `
                <div class="document-item" data-doc-id="${doc.id}">
                    <div class="document-name" title="${doc.original_filename}">
                        ${this.truncateFilename(doc.original_filename, 25)}
                    </div>
                    <div class="document-meta">
                        <span>
                            ${doc.page_count || 0} pages • ${doc.chunk_count || 0} chunks
                        </span>
                        <div class="document-actions">
                            <button class="btn-document-action btn-document-delete" 
                                    onclick="app.deleteDocument(${doc.id})"
                                    title="Delete document">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </div>
                    <div class="document-status">
                        <span class="badge ${doc.processed ? 'bg-success' : 'bg-warning'}">
                            ${doc.processed ? 'Processed' : 'Processing...'}
                        </span>
                    </div>
                </div>
            `).join('');
        }
        
        // Refresh Feather icons
        feather.replace();
    }

    truncateFilename(filename, maxLength) {
        if (filename.length <= maxLength) return filename;
        const ext = filename.split('.').pop();
        const nameLength = maxLength - ext.length - 4; // account for "..." and "."
        return filename.substring(0, nameLength) + '...' + ext;
    }

    async uploadDocument(file) {
        if (file.size > 16 * 1024 * 1024) {
            this.showAlert('File too large. Maximum size is 16MB.', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        const progressContainer = document.querySelector('.upload-progress');
        const progressBar = progressContainer.querySelector('.progress-bar');
        progressContainer.style.display = 'block';
        progressBar.style.width = '20%';

        try {
            const response = await fetch('/upload_document', {
                method: 'POST',
                body: formData
            });

            progressBar.style.width = '70%';
            const data = await response.json();
            progressBar.style.width = '100%';

            if (data.success) {
                this.showAlert(data.message, 'success');
                this.loadDocuments();
                this.refreshStats();
            } else {
                this.showAlert(data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Upload failed: ' + error.message, 'danger');
        } finally {
            // Hide progress after delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
            }, 1000);
        }
    }

    async deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            const response = await fetch(`/delete_document/${docId}`, {
                method: 'DELETE'
            });
            const data = await response.json();

            if (data.success) {
                this.showAlert(data.message, 'success');
                this.loadDocuments();
                this.refreshStats();
            } else {
                this.showAlert(data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Delete failed: ' + error.message, 'danger');
        }
    }

    async sendMessage() {
        if (this.isLoading) return;

        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Clear input and add user message
        input.value = '';
        this.addMessage('user', message);

        // Show loading
        this.setLoading(true);
        const loadingMessage = this.addMessage('assistant', 'Searching documents and generating response...', true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove loading message
            loadingMessage.remove();

            if (data.success) {
                this.addMessage('assistant', data.response.content, false, data.response);
            } else {
                this.addMessage('assistant', `Error: ${data.error}`, false, { error: true });
            }
        } catch (error) {
            loadingMessage.remove();
            this.addMessage('assistant', `Network error: ${error.message}`, false, { error: true });
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(role, content, isLoading = false, metadata = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        let headerContent = '';
        if (role === 'assistant') {
            headerContent = `
                <div class="message-header">
                    <i data-feather="cpu"></i>
                    <strong>Assistant</strong>
                    ${isLoading ? '<span class="spinner ms-2"></span>' : ''}
                </div>
            `;
        } else if (role === 'user') {
            headerContent = `
                <div class="message-header">
                    <i data-feather="user"></i>
                    <strong>You</strong>
                </div>
            `;
        }

        let contextInfo = '';
        if (metadata && !metadata.error && !isLoading) {
            contextInfo = `
                <div class="message-context">
                    <div class="context-item">
                        <i data-feather="search"></i>
                        <span>Found ${metadata.chunks_found || 0} relevant document chunks</span>
                    </div>
                    <div class="context-item">
                        <i data-feather="cpu"></i>
                        <span>Model: ${metadata.model || 'unknown'}</span>
                    </div>
                    ${metadata.context_used ? '<div class="context-item"><i data-feather="book-open"></i><span>Used document context</span></div>' : ''}
                    ${metadata.referenced_documents && metadata.referenced_documents.length > 0 ? `
                        <div class="referenced-docs">
                            <strong>Referenced documents:</strong><br>
                            ${metadata.referenced_documents.map(doc => 
                                `<span class="doc-reference">${doc.filename}</span>`
                            ).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                ${headerContent}
                <div class="message-text">${this.formatText(content)}</div>
                ${contextInfo}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Refresh Feather icons
        feather.replace();

        return messageDiv;
    }

    formatText(text) {
        // Basic markdown-style formatting
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Handle lists
        formatted = formatted.replace(/^\- (.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        return `<p>${formatted}</p>`;
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendButton = document.getElementById('send-button');
        const messageInput = document.getElementById('message-input');
        
        if (loading) {
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="spinner"></span>';
            messageInput.disabled = true;
        } else {
            sendButton.disabled = false;
            sendButton.innerHTML = '<i data-feather="send"></i>';
            messageInput.disabled = false;
            feather.replace();
        }
    }

    async saveSettings() {
        const apiKey = document.getElementById('api-key').value.trim();
        const model = document.getElementById('model-select').value;

        if (!apiKey) {
            this.showAlert('Please enter your OpenRouter API key', 'warning');
            return;
        }

        try {
            const response = await fetch('/test_openrouter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey, model })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Settings saved successfully!', 'success');
                document.getElementById('api-key').placeholder = 'API key configured';
                document.getElementById('api-key').value = '';
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
                modal.hide();
            } else {
                this.showAlert(data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to save settings: ' + error.message, 'danger');
        }
    }

    async testAPI() {
        const apiKey = document.getElementById('api-key').value.trim();
        const model = document.getElementById('model-select').value;
        const resultDiv = document.getElementById('api-test-result');

        if (!apiKey) {
            this.showAlert('Please enter your API key first', 'warning');
            return;
        }

        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<div class="alert alert-info">Testing connection...</div>';

        try {
            const response = await fetch('/test_openrouter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey, model })
            });

            const data = await response.json();

            if (data.success) {
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>✓ Connection successful!</strong><br>
                        Model: ${data.model}<br>
                        Response: ${data.response}
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>✗ Connection failed</strong><br>
                        ${data.error}
                    </div>
                `;
            }
        } catch (error) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>✗ Network error</strong><br>
                    ${error.message}
                </div>
            `;
        }
    }

    async refreshStats() {
        try {
            const response = await fetch('/get_stats');
            const data = await response.json();

            if (data.success) {
                document.getElementById('stat-documents').textContent = data.stats.total_documents || 0;
                document.getElementById('stat-chunks').textContent = data.stats.total_chunks || 0;
                document.getElementById('stat-ready').textContent = data.stats.search_ready ? 'Yes' : 'No';
            }
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }

    async clearChat() {
        if (!confirm('Clear all chat messages?')) return;

        try {
            const response = await fetch('/clear_chat', {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                // Clear messages except system message
                const messagesContainer = document.getElementById('chat-messages');
                const systemMessage = messagesContainer.querySelector('.system-message');
                messagesContainer.innerHTML = '';
                messagesContainer.appendChild(systemMessage);
                
                this.showAlert('Chat cleared', 'success');
            } else {
                this.showAlert(data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to clear chat: ' + error.message, 'danger');
        }
    }

    async clearSession() {
        if (!confirm('Clear all data including API keys and chat history?')) return;

        try {
            const response = await fetch('/clear_session', {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                location.reload();
            } else {
                this.showAlert(data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to clear session: ' + error.message, 'danger');
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(alertDiv);

        // Position at top
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '70px';
        alertDiv.style.left = '50%';
        alertDiv.style.transform = 'translateX(-50%)';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Global functions for onclick handlers
function sendMessage() {
    app.sendMessage();
}

function clearChat() {
    app.clearChat();
}

function clearSession() {
    app.clearSession();
}

function testAPI() {
    app.testAPI();
}

function refreshStats() {
    app.refreshStats();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PilotRAG();
});