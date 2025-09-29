from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4.1-mini-2025-04-14"
    embedding_model: str = "text-embedding-ada-002"
    
    # Google Calendar Configuration
    google_calendar_enabled: bool = True
    pat: str = os.getenv("PAT", "")
    
    # FAISS Configuration
    faiss_index_path: str = "./data/faiss_store"
    
    # RAG Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 3
    similarity_threshold: float = 0.3
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()