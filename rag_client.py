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
        self.search_engine = None  # Will be set by get_vector_search()
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
6. IMPORTANT: When users ask follow-up questions, maintain awareness of the document context from our previous discussion and build upon it naturally
7. For vague follow-ups like "tell me more" or "what else", expand on the document topics we were just discussing

Format your responses clearly with proper paragraphs and bullet points when helpful."""
    
    def chat_with_rag(self, message: str, conversation_history: Optional[List[Dict]] = None, 
                      model: Optional[str] = None, max_chunks: int = 5,
                      last_referenced_docs: Optional[List[int]] = None,
                      last_chunks_used: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate response using RAG: Retrieve relevant documents then generate answer
        """
        try:
            # Step 1: Retrieve relevant document chunks  
            if self.search_engine is None:
                from routes import get_vector_search
                self.search_engine = get_vector_search()
            
            # Enhanced search with document context persistence
            search_query = self._build_enhanced_search_query(message, conversation_history)
            relevant_chunks = self.search_engine.search(search_query, top_k=max_chunks)
            
            # If message is ambiguous and we have previous chunks, boost with previous context
            if self._is_ambiguous_followup(message) and last_chunks_used:
                logger.info(f"Detected ambiguous follow-up: '{message}', including previous context")
                relevant_chunks = self._merge_with_previous_context(relevant_chunks, last_chunks_used)
            
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
                    'referenced_documents': referenced_docs,
                    'chunks_used': [chunk.text_content for chunk, _ in relevant_chunks[:3]]  # Store top 3 chunk contents
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
            if self.search_engine is None:
                from routes import get_vector_search
                self.search_engine = get_vector_search()
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
            
            # Get the global search engine instance
            if self.search_engine is None:
                from routes import get_vector_search
                self.search_engine = get_vector_search()
            
            return {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'search_ready': bool(self.search_engine.vectorizer and hasattr(self.search_engine, 'chunks') and len(self.search_engine.chunks) > 0)
            }
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {'error': str(e)}
    
    def _build_enhanced_search_query(self, current_message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """Build enhanced search query that includes context from recent conversation"""
        if not conversation_history or len(conversation_history) < 2:
            return current_message
        
        # Get recent conversation context (last 2-3 messages)
        recent_messages = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history
        
        # Extract key terms from recent user messages
        context_terms = []
        for msg in recent_messages:
            if msg.get('role') == 'user':
                # Extract important words (longer than 3 chars, not common words)
                words = msg.get('content', '').split()
                important_words = [w.strip('.,!?') for w in words 
                                 if len(w) > 3 and w.lower() not in ['what', 'when', 'where', 'how', 'why', 'which', 'that', 'this', 'with', 'from', 'they', 'have', 'been', 'will', 'would', 'could', 'should']]
                context_terms.extend(important_words[:3])  # Max 3 terms per message
        
        # Combine current message with context terms
        if context_terms:
            # Remove duplicates and limit total terms
            unique_terms = list(set(context_terms))[:5]  
            enhanced_query = f"{current_message} {' '.join(unique_terms)}"
            logger.info(f"Enhanced search query: {current_message} -> {enhanced_query}")
            return enhanced_query
        
        return current_message
    
    def _is_ambiguous_followup(self, message: str) -> bool:
        """Check if message is an ambiguous follow-up that needs previous context"""
        message_lower = message.lower().strip()
        
        # Short messages or common follow-up phrases
        ambiguous_patterns = [
            'tell me more', 'more', 'what else', 'continue', 'go on', 'and?',
            'explain', 'details', 'elaborate', 'expand', 'further',
            'what about', 'how about', 'also', 'additionally'
        ]
        
        # Very short messages (less than 15 chars) or matches patterns
        is_short = len(message_lower) < 15
        matches_pattern = any(pattern in message_lower for pattern in ambiguous_patterns)
        
        return is_short or matches_pattern
    
    def _merge_with_previous_context(self, current_chunks: List[tuple], previous_chunks: List[str]) -> List[tuple]:
        """Merge current search results with previous context chunks"""
        try:
            # If we don't have enough current chunks, include previous context
            if len(current_chunks) < 3 and previous_chunks:
                logger.info(f"Including {len(previous_chunks)} previous chunks for context continuity")
                
                # Add previous chunks as pseudo-chunks (they don't have scores, so give them medium relevance)
                for prev_chunk in previous_chunks[:2]:  # Only use top 2 from previous
                    # Create a simple chunk-like object
                    pseudo_chunk = type('PreviousChunk', (), {
                        'text_content': prev_chunk,
                        'document_id': 1,  # Use default document ID
                        'page_number': 1
                    })()
                    current_chunks.append((pseudo_chunk, 0.5))  # Medium relevance score
            
            return current_chunks
            
        except Exception as e:
            logger.error(f"Error merging with previous context: {str(e)}")
            return current_chunks