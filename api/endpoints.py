# api/endpoints.py
import time
from fastapi import APIRouter, HTTPException, Depends, status
from models.transcript import TranscriptRequest
from models.appointment import AppointmentExtractionResponse
from services.rag_service import RAGService
from services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_rag_service() -> RAGService:
    return RAGService()

def get_llm_service() -> LLMService:
    return LLMService()

@router.post("/extract-appointments", response_model=AppointmentExtractionResponse)
async def extract_appointments(
    request: TranscriptRequest,
    rag_service: RAGService = Depends(get_rag_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Extract appointment information from transcript using FAISS RAG"""
    start_time = time.time()
    
    try:
        # Process and store in FAISS
        success = rag_service.process_and_store_transcript(
            transcript_text=request.transcript,
            session_id=request.session_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No appointment content found in transcript"
            )
        
        # Retrieve relevant context using FAISS
        context = rag_service.retrieve_relevant_context()
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No appointment-related context retrieved"
            )
        
        # Extract using LLM
        extracted_appointments = llm_service.extract_appointments(context)
        
        if not extracted_appointments:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract appointment information"
            )
        
        processing_time = time.time() - start_time
        
        return AppointmentExtractionResponse(
            success=True,
            data=extracted_appointments,
            message=f"Extracted {len(extracted_appointments.appointments)} appointments",
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "appointment-extractor-faiss"}

@router.get("/faiss-info")
async def get_faiss_info(rag_service: RAGService = Depends(get_rag_service)):
    """Get FAISS index information"""
    return rag_service.faiss_service.get_index_info()
