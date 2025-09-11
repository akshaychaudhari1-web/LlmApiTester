import os
import re
import logging
from typing import List, Tuple
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app import db
from models import Document, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles PDF processing and text extraction"""
    
    def __init__(self):
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
    
    def process_pdf(self, file_path: str, filename: str, original_filename: str) -> Document:
        """Process a PDF file and create document record"""
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document record
            document = Document()
            document.filename = filename
            document.original_filename = original_filename
            document.file_path = file_path
            document.file_size = file_size
            document.processed = False
            db.session.add(document)
            db.session.commit()
            
            # Extract text from PDF
            text_chunks = self._extract_text_from_pdf(file_path)
            
            # Create chunks
            self._create_chunks(document, text_chunks)
            
            # Mark as processed
            document.processed = True
            document.page_count = len(text_chunks)
            db.session.commit()
            
            logger.info(f"Successfully processed PDF: {original_filename}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing PDF {original_filename}: {str(e)}")
            # Clean up on error
            if 'document' in locals() and hasattr(document, 'id') and document.id:
                try:
                    db.session.delete(document)
                    db.session.commit()
                except:
                    pass
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> List[Tuple[int, str]]:
        """Extract text from PDF file, return list of (page_number, text)"""
        text_chunks = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        # Clean up text
                        text = self._clean_text(text)
                        text_chunks.append((page_num, text))
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
        
        return text_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep automotive-relevant punctuation
        text = re.sub(r'[^\w\s\-\.\,\(\)\%\$\/]', '', text)
        
        # Remove very short lines (likely formatting artifacts)
        lines = text.split('\n')
        clean_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return ' '.join(clean_lines).strip()
    
    def _create_chunks(self, document: Document, text_pages: List[Tuple[int, str]]):
        """Split text into overlapping chunks and store them"""
        chunk_index = 0
        
        for page_num, page_text in text_pages:
            # Split page into chunks
            chunks = self._split_text_into_chunks(page_text)
            
            for chunk_text in chunks:
                if len(chunk_text.strip()) > 50:  # Only store meaningful chunks
                    chunk = DocumentChunk()
                    chunk.document_id = document.id
                    chunk.chunk_index = chunk_index
                    chunk.page_number = page_num
                    chunk.text_content = chunk_text.strip()
                    db.session.add(chunk)
                    chunk_index += 1
        
        db.session.commit()
        logger.info(f"Created {chunk_index} chunks for document {document.filename}")
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to break at word boundary
            chunk_end = text.rfind(' ', start, end)
            if chunk_end == -1 or chunk_end <= start:
                chunk_end = end
            
            chunks.append(text[start:chunk_end])
            start = chunk_end - self.chunk_overlap
            
            # Ensure we make progress
            if start <= 0:
                start = chunk_end
        
        return chunks

class VectorSearchEngine:
    """Simple vector search using TF-IDF and cosine similarity"""
    
    def __init__(self):
        self.vectorizer = None
        self.document_vectors = None
        self.chunks = []
        # Don't initialize during import - wait for app context
    
    def _initialize(self):
        """Initialize the search engine with existing documents"""
        try:
            self.refresh_index()
        except Exception as e:
            logger.warning(f"Could not initialize search index: {e}")
            # Will be initialized on first use
    
    def refresh_index(self):
        """Rebuild the search index with all document chunks"""
        try:
            # Get all processed chunks
            self.chunks = DocumentChunk.query.join(Document).filter(
                Document.processed == True
            ).all()
        except Exception as e:
            logger.warning(f"Could not query documents: {e}")
            self.chunks = []
            return
        
        if not self.chunks:
            logger.info("No processed documents found for indexing")
            return
        
        # Extract text content
        texts = [chunk.text_content for chunk in self.chunks]
        
        # Create TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams
            min_df=1,
            max_df=0.95
        )
        
        self.document_vectors = self.vectorizer.fit_transform(texts)
        logger.info(f"Indexed {len(self.chunks)} document chunks")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for relevant document chunks"""
        if not self.vectorizer or not self.chunks:
            logger.warning("Search index not initialized")
            return []
        
        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            # Get top k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    chunk = self.chunks[idx]
                    score = similarities[idx]
                    results.append((chunk, score))
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_automotive_keywords(self) -> List[str]:
        """Get automotive-specific keywords for filtering"""
        return [
            'car', 'automobile', 'vehicle', 'engine', 'motor', 'transmission',
            'brake', 'suspension', 'steering', 'tire', 'wheel', 'battery',
            'fuel', 'oil', 'maintenance', 'repair', 'diagnostic', 'performance',
            'safety', 'airbag', 'seatbelt', 'emissions', 'hybrid', 'electric',
            'combustion', 'cylinder', 'piston', 'alternator', 'starter',
            'radiator', 'cooling', 'exhaust', 'muffler', 'catalytic',
            'toyota', 'honda', 'ford', 'chevrolet', 'bmw', 'mercedes',
            'audi', 'volkswagen', 'nissan', 'hyundai', 'mazda', 'subaru'
        ]
    
    def is_automotive_related(self, text: str) -> bool:
        """Check if text is automotive-related"""
        automotive_keywords = self.get_automotive_keywords()
        text_lower = text.lower()
        
        # Check for automotive keywords
        automotive_matches = sum(1 for keyword in automotive_keywords if keyword in text_lower)
        
        # If more than 2 automotive keywords, consider it automotive-related
        return automotive_matches >= 2