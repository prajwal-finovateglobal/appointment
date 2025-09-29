import json
import re
from typing import List, Dict, Any, Union
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class TranscriptProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.appointment_keywords = [
            "appointment", "schedule", "book", "meeting", "visit", "consultation",
            "available", "time", "date", "tomorrow", "today", "next week",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "am", "pm", "morning", "afternoon", "evening", "o'clock"
        ]
    
    def parse_transcript(self, transcript_text: str) -> List[Dict[str, Any]]:
        """Parse transcript text or JSON into structured format - handles any schema"""
        try:
            # Try JSON parsing first
            transcript_data = json.loads(transcript_text)
            return self._normalize_transcript_data(transcript_data)
        except json.JSONDecodeError:
            return self._parse_plain_text(transcript_text)
    
    def _normalize_transcript_data(self, data: Union[Dict, List]) -> List[Dict[str, Any]]:
        """Normalize any transcript data structure to a common format"""
        if isinstance(data, list):
            # Handle list of objects (most common case)
            normalized = []
            for item in data:
                if isinstance(item, dict):
                    normalized.append(self._normalize_single_item(item))
                else:
                    # Handle primitive values in list
                    normalized.append({
                        "text": str(item),
                        "speaker": "unknown",
                        "timestamp": "",
                        "confidence": 0.9
                    })
            return normalized
        elif isinstance(data, dict):
            # Handle single object or nested structure
            if "transcript" in data:
                return self._normalize_transcript_data(data["transcript"])
            elif "messages" in data:
                return self._normalize_transcript_data(data["messages"])
            elif "conversation" in data:
                return self._normalize_transcript_data(data["conversation"])
            else:
                # Single message object
                return [self._normalize_single_item(data)]
        else:
            # Handle primitive values
            return [{
                "text": str(data),
                "speaker": "unknown", 
                "timestamp": "",
                "confidence": 0.9
            }]
    
    def _normalize_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single transcript item to standard format"""
        normalized = {
            "text": "",
            "speaker": "unknown",
            "timestamp": "",
            "confidence": 0.9
        }
        
        # Map various field names to standard fields
        text_fields = ["text", "content", "message", "body", "transcript", "utterance"]
        speaker_fields = ["speaker", "sender", "user", "agent", "role", "from"]
        timestamp_fields = ["timestamp", "time", "created_at", "date", "datetime"]
        confidence_fields = ["confidence", "score", "probability"]
        
        # Extract text content
        for field in text_fields:
            if field in item and item[field]:
                normalized["text"] = str(item[field])
                break
        
        # Extract speaker
        for field in speaker_fields:
            if field in item and item[field]:
                normalized["speaker"] = str(item[field]).lower()
                break
        
        # Extract timestamp
        for field in timestamp_fields:
            if field in item and item[field]:
                normalized["timestamp"] = str(item[field])
                break
        
        # Extract confidence
        for field in confidence_fields:
            if field in item and item[field]:
                try:
                    normalized["confidence"] = float(item[field])
                except (ValueError, TypeError):
                    normalized["confidence"] = 0.9
                break
        
        # If no text found, try to use any string value
        if not normalized["text"]:
            for key, value in item.items():
                if isinstance(value, str) and value.strip():
                    normalized["text"] = value
                    break
        
        return normalized
    
    def _parse_plain_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse plain text transcript"""
        segments = []
        lines = text.strip().split('\\n')
        
        for i, line in enumerate(lines):
            if line.strip():
                # Pattern matching for speaker identification
                speaker_match = re.match(r'^(Agent|Customer|agent|customer)\\s*[:|-]\\s*(.+)', line.strip())
                if speaker_match:
                    speaker = speaker_match.group(1).lower()
                    text_content = speaker_match.group(2).strip()
                else:
                    speaker = "unknown"
                    text_content = line.strip()
                
                segments.append({
                    "timestamp": f"00:{i:02d}:00",
                    "speaker": speaker,
                    "text": text_content,
                    "confidence": 0.95
                })
        
        return segments
    
    def extract_appointment_chunks(self, segments: List[Dict[str, Any]]) -> List[Document]:
        """Extract appointment-related conversation chunks"""
        relevant_segments = []
        
        # Find segments containing appointment keywords
        for segment in segments:
            text_lower = segment["text"].lower()
            if any(keyword in text_lower for keyword in self.appointment_keywords):
                relevant_segments.append(segment)
        
        if not relevant_segments:
            return []
        
        # Group consecutive relevant segments
        grouped_conversations = self._group_consecutive_segments(relevant_segments, segments)
        
        # Create documents for FAISS
        documents = []
        for i, conversation in enumerate(grouped_conversations):
            text = self._format_conversation(conversation)
            doc = Document(
                page_content=text,
                metadata={
                    "chunk_id": i,
                    "segment_count": len(conversation),
                    "timestamp_start": conversation[0]["timestamp"] if conversation else "00:00:00"
                }
            )
            documents.append(doc)
        
        return documents
    
    def _group_consecutive_segments(self, relevant_segments: List[Dict], all_segments: List[Dict]) -> List[List[Dict]]:
        """Group consecutive appointment-related segments"""
        if not relevant_segments:
            return []
        
        grouped = []
        current_group = []
        
        # Create index mapping
        segment_indices = {id(seg): i for i, seg in enumerate(all_segments)}
        relevant_indices = [segment_indices.get(id(seg), -1) for seg in relevant_segments]
        
        for i, segment in enumerate(relevant_segments):
            if not current_group:
                current_group = [segment]
            else:
                # Check if segments are close (within 3 segments)
                prev_idx = relevant_indices[i-1] if i > 0 else -1
                curr_idx = relevant_indices[i]
                
                if curr_idx - prev_idx <= 3:
                    current_group.append(segment)
                else:
                    grouped.append(current_group)
                    current_group = [segment]
        
        if current_group:
            grouped.append(current_group)
        
        return grouped
    
    def _format_conversation(self, segments: List[Dict[str, Any]]) -> str:
        """Format conversation segments into readable text"""
        formatted_lines = []
        for segment in segments:
            speaker = segment.get("speaker", "unknown").capitalize()
            text = segment.get("text", "")
            timestamp = segment.get("timestamp", "")
            formatted_lines.append(f"[{timestamp}] {speaker}: {text}")
        
        return "\\n".join(formatted_lines)