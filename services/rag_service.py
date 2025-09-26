# services/rag_service.py
from typing import List, Optional
from services.faiss_service import FAISSService
from utils.text_processing import TranscriptProcessor
from utils.config import settings
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.faiss_service = FAISSService()
        self.transcript_processor = TranscriptProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
    
    def process_and_store_transcript(self, transcript_text: str, session_id: str = None) -> bool:
        """Process transcript and store in FAISS"""
        try:
            # Parse transcript
            segments = self.transcript_processor.parse_transcript(transcript_text)
            
            # Store the full transcript content for direct LLM processing
            self._last_transcript_content = self._format_full_transcript(segments)
            
            # Extract appointment chunks
            appointment_docs = self.transcript_processor.extract_appointment_chunks(segments)
            
            if appointment_docs:
                # Add session metadata
                for doc in appointment_docs:
                    if session_id:
                        doc.metadata["session_id"] = session_id
                
                # Store in FAISS (for future optimization)
                self.faiss_service.add_documents(appointment_docs)
                return True
            else:
                logger.warning("No appointment content found, but will use full transcript")
                return True  # Still return True since we have the full transcript
                
        except Exception as e:
            logger.error(f"Failed to process transcript: {e}")
            return False
    
    def _format_full_transcript(self, segments) -> str:
        """Format the full transcript for LLM processing"""
        formatted_lines = []
        for segment in segments:
            speaker = segment.get("speaker", "unknown").capitalize()
            text = segment.get("text", "")
            timestamp = segment.get("timestamp", "")
            formatted_lines.append(f"[{timestamp}] {speaker}: {text}")
        
        return "\n".join(formatted_lines)
    
    def retrieve_relevant_context(self, query: str = "appointment schedule time date") -> str:
        """Retrieve appointment context - temporarily bypassing FAISS for direct transcript processing"""
        try:
            # For now, bypass FAISS and return the stored transcript content
            # This will be optimized later with proper FAISS similarity search
            if hasattr(self, '_last_transcript_content'):
                return self._last_transcript_content
            
            # Fallback: try FAISS similarity search
            results = self.faiss_service.similarity_search(query)
            
            if not results:
                # Fallback to similarity search with scores
                results_with_scores = self.faiss_service.similarity_search_with_score(query)
                if not results_with_scores:
                    return ""
                
                context_parts = []
                for doc, score in results_with_scores:
                    context_parts.append(f"Context (Score: {score:.3f}):\n{doc.page_content}")
                return "\n\n---\n\n".join(context_parts)
            
            context_parts = []
            for doc in results:
                context_parts.append(f"Context:\n{doc.page_content}")
            
            return "\n\n---\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return ""
