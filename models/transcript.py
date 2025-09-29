from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union

class TranscriptRequest(BaseModel):
    transcript: Union[str, Dict[str, Any], List[Any]] = Field(..., description="Raw transcript text, JSON object, or any structured data")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('transcript', mode='before')
    @classmethod
    def convert_transcript(cls, v):
        """Convert transcript to appropriate format - accepts any structure"""
        if isinstance(v, str):
            return v
        elif isinstance(v, (dict, list)):
            # Convert any dict/list to JSON string for processing
            import json
            return json.dumps(v)
        else:
            return str(v)
