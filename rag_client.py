import os
import logging
import requests
from typing import List, Dict, Any, Optional
from document_processor import VectorSearchEngine
from models import DocumentChunk, Document

logger = logging.getLogger(__name__)

class RAGClient:
    """RAG (Retrieval-Augmented Generation) client that combines document search with LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.search_engine = VectorSearchEngine()
        self.default_model = "openrouter/sonoma-sky-alpha"
        
        # Automotive system prompt for RAG
        self.system_prompt = """You are an automotive expert assistant with access to technical documentation. You ONLY discuss topics related to:

- Cars, trucks, motorcycles, and other vehicles
- Automotive technology, engines, and mechanical systems  
- Vehicle maintenance, repair, and troubleshooting
- Car manufacturers, models, and automotive history
- Racing, motorsports, and automotive performance
- Electric vehicles, hybrids, and automotive innovations
- Vehicle safety, regulations, and automotive industry news

When answering questions:
1. Use the provided document context to give accurate, detailed answers
2. If the documents contain relevant information, cite the specific details
3. If the documents don't contain enough information, say so and provide general automotive knowledge
4. Always stay focused on automotive topics
5. If asked about non-automotive topics, politely redirect to automotive discussions

Format your responses clearly with proper paragraphs and bullet points when helpful."""
    
    def chat_with_rag(self, message: str, conversation_history: Optional[List[Dict]] = None, 
                      model: Optional[str] = None, max_chunks: int = 5) -> Dict[str, Any]:
        """
        Generate response using RAG: Retrieve relevant documents then generate answer
        """
        try:
            # Step 1: Retrieve relevant document chunks
            relevant_chunks = self.search_engine.search(message, top_k=max_chunks)
            
            # Step 2: Build context from retrieved documents
            context = self._build_context(relevant_chunks)
            
            # Step 3: Generate response with context
            response = self._generate_response(
                message=message,
                context=context,
                conversation_history=conversation_history or [],
                model=model or self.default_model
            )
            
            # Step 4: Extract referenced document info
            referenced_docs = self._extract_document_info(relevant_chunks)
            
            return {
                'success': True,
                'response': {
                    'content': response,
                    'model': model or self.default_model,
                    'context_used': bool(context),
                    'chunks_found': len(relevant_chunks),
                    'referenced_documents': referenced_docs
                }
            }
            
        except Exception as e:
            logger.error(f"RAG chat error: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to generate response: {str(e)}"
            }
    
    def _build_context(self, relevant_chunks: List[tuple]) -> str:
        """Build context string from retrieved document chunks"""
        if not relevant_chunks:
            return ""
        
        context_parts = []
        context_parts.append("=== RELEVANT DOCUMENT INFORMATION ===\n")
        
        for i, (chunk, score) in enumerate(relevant_chunks, 1):
            # Get document info
            document = Document.query.get(chunk.document_id)
            if document is None:
                continue
                
            context_parts.append(
                f"Source {i}: {document.original_filename} (Page {chunk.page_number})\n"
                f"Content: {chunk.text_content}\n"
                f"Relevance Score: {score:.3f}\n"
            )
        
        context_parts.append("=== END DOCUMENT INFORMATION ===\n")
        return "\n".join(context_parts)
    
    def _generate_response(self, message: str, context: str, 
                          conversation_history: List[Dict], model: str) -> str:
        """Generate LLM response with document context"""
        
        # Build messages array
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current message with context
        if context:
            user_message = f"{context}\n\nUser Question: {message}\n\nPlease answer based on the document information provided above, staying focused on automotive topics."
        else:
            user_message = message
        
        messages.append({"role": "user", "content": user_message})
        
        # Make API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._get_referer(),
            "X-Title": "Pilot RAG - Automotive Document Assistant"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result['choices'][0]['message']['content']
    
    def _extract_document_info(self, relevant_chunks: List[tuple]) -> List[Dict]:
        """Extract document information for response metadata"""
        doc_info = []
        seen_docs = set()
        
        for chunk, score in relevant_chunks:
            if chunk.document_id not in seen_docs:
                document = Document.query.get(chunk.document_id)
                if document is not None:
                    doc_info.append({
                        'id': document.id,
                        'filename': document.original_filename,
                        'relevance_score': score
                    })
                    seen_docs.add(chunk.document_id)
        
        return doc_info
    
    def _get_referer(self) -> str:
        """Get appropriate referer for API calls"""
        if 'REPLIT_DEPLOYMENT' in os.environ:
            return f"https://{os.environ.get('REPL_SLUG', 'pilot-rag')}.{os.environ.get('REPL_OWNER', 'user')}.replit.app"
        return "http://localhost:5001"
    
    def test_connection(self, api_key: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Test OpenRouter API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self._get_referer(),
                "X-Title": "Pilot RAG - Connection Test"
            }
            
            payload = {
                "model": model or self.default_model,
                "messages": [
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'Connection successful' if you can read this."}
                ],
                "max_tokens": 10
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'API connection successful',
                    'model': model or self.default_model,
                    'response': result['choices'][0]['message']['content']
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection failed: {str(e)}"
            }
    
    def refresh_search_index(self):
        """Refresh the document search index"""
        try:
            self.search_engine.refresh_index()
            logger.info("Search index refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh search index: {str(e)}")
            return False
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents"""
        try:
            total_docs = Document.query.filter_by(processed=True).count()
            total_chunks = DocumentChunk.query.join(Document).filter(
                Document.processed == True
            ).count()
            
            return {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'search_ready': bool(self.search_engine.vectorizer)
            }
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {'error': str(e)}