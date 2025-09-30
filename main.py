# main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router
from api import availability_router, booking_router
from utils.config import settings

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting Appointment Extraction API and Google Calendar...")
    logging.info(f"RAG Index Path: {settings.faiss_index_path}")
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="Appointment Extraction API and Google Calendar",
    description="Extract appointments from transcripts using RAG and Google Calendar integration",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["appointments-transcripts-extraction"])
app.include_router(availability_router, tags=["google-calendar-avilability"])
app.include_router(booking_router, tags=["google-calendar-booking"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
