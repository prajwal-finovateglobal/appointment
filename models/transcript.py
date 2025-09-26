from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union

class TranscriptRequest(BaseModel):
    transcript: Union[str, List[Dict[str, Any]]] = Field(..., description="Raw transcript text, JSON string, or structured array")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('transcript', mode='before')
    @classmethod
    def convert_transcript(cls, v):
        """Convert transcript to appropriate format"""
        if isinstance(v, str):
            return v
        elif isinstance(v, list):
            # Convert list to JSON string for processing
            import json
            return json.dumps(v)
        else:
            return str(v)
