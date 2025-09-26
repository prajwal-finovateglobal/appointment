import os
import pickle
from typing import List, Optional, Tuple
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from utils.config import settings
import logging

logger = logging.getLogger(__name__)

class FAISSService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        self.vector_store: Optional[FAISS] = None
        self.index_path = settings.faiss_index_path
        
        # Create directory
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize FAISS
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        faiss_index_file = os.path.join(self.index_path, "index.faiss")
        faiss_pkl_file = os.path.join(self.index_path, "index.pkl")
        
        if os.path.exists(faiss_index_file) and os.path.exists(faiss_pkl_file):
            try:
                self.vector_store = FAISS.load_local(
                    self.index_path, 
                    self.embeddings,
                    index_name="index",
                    allow_dangerous_deserialization=True
                )
                logger.info("Loaded existing FAISS index")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
                self._create_empty_index()
        else:
            self._create_empty_index()
    
    def _create_empty_index(self):
        """Create empty FAISS index"""
        # Create dummy document to initialize
        dummy_doc = Document(
            page_content="initialization document for FAISS index",
            metadata={"type": "init", "chunk_id": -1}
        )
        
        self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
        self._save_index()
        logger.info("Created new FAISS index")
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to FAISS index"""
        try:
            if not documents:
                logger.warning("No documents to add")
                return False
            
            if self.vector_store is None:
                logger.error("FAISS index not initialized")
                return False
            
            # Filter out initialization documents
            valid_docs = [doc for doc in documents if doc.metadata.get("type") != "init"]
            
            if valid_docs:
                self.vector_store.add_documents(valid_docs)
                self._save_index()
                logger.info(f"Added {len(valid_docs)} documents to FAISS index")
                return True
            else:
                logger.warning("No valid documents to add")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add documents to FAISS: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """Perform similarity search"""
        try:
            if self.vector_store is None:
                logger.error("FAISS index not initialized")
                return []
            
            k = k or settings.top_k_results
            logger.info(f"Performing similarity search with query: '{query}', k={k}")
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Raw similarity search returned {len(results)} documents")
            
            # Filter out initialization documents
            filtered_results = [doc for doc in results if doc.metadata.get("type") != "init"]
            
            logger.info(f"Found {len(filtered_results)} similar documents after filtering")
            for i, doc in enumerate(filtered_results):
                logger.info(f"Document {i}: {doc.page_content[:100]}...")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"FAISS similarity search failed: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """Perform similarity search with confidence scores"""
        try:
            if self.vector_store is None:
                logger.error("FAISS index not initialized")
                return []
            
            k = k or settings.top_k_results
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Remove init documents only (no threshold filtering)
            filtered_results = []
            for doc, score in results:
                if doc.metadata.get("type") != "init":
                    filtered_results.append((doc, score))
            
            logger.info(f"Found {len(filtered_results)} documents (top-k results)")
            return filtered_results
            
        except Exception as e:
            logger.error(f"FAISS similarity search with score failed: {e}")
            return []
    
    def _save_index(self):
        """Save FAISS index to disk"""
        try:
            if self.vector_store:
                self.vector_store.save_local(self.index_path, index_name="index")
                logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    def clear_index(self):
        """Clear FAISS index and recreate empty one"""
        try:
            self._create_empty_index()
            logger.info("FAISS index cleared and recreated")
        except Exception as e:
            logger.error(f"Failed to clear FAISS index: {e}")
    
    def get_index_info(self) -> dict:
        """Get information about the FAISS index"""
        try:
            if self.vector_store is None:
                return {"status": "not_initialized", "document_count": 0}
            
            # Get document count (approximate)
            doc_count = self.vector_store.index.ntotal if hasattr(self.vector_store, 'index') else 0
            
            return {
                "status": "initialized",
                "document_count": doc_count,
                "index_path": self.index_path,
                "embedding_model": settings.embedding_model
            }
        except Exception as e:
            logger.error(f"Failed to get FAISS index info: {e}")
            return {"status": "error", "error": str(e)}