# services/llm_service.py
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from models.appointment import ExtractedAppointments
from utils.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.output_parser = PydanticOutputParser(pydantic_object=ExtractedAppointments)
    
    def extract_appointments(self, context: str) -> Optional[ExtractedAppointments]:
        """Extract appointments using OpenAI LLM"""
        try:
            system_prompt = self._create_system_prompt()
            human_prompt = f"Extract appointment information from:\n\n{context}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            
            try:
                extracted_data = self.output_parser.parse(response.content)
                extracted_data.confidence_score = self._calculate_confidence(context, extracted_data)
                return extracted_data
            except Exception as parse_error:
                logger.warning(f"Failed to parse structured output: {parse_error}")
                return self._manual_parse_response(response.content)
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None
    
    def _create_system_prompt(self) -> str:
        format_instructions = self.output_parser.get_format_instructions()
        
        return f"""You are an expert at extracting appointment information from customer service transcripts.

Extract ALL appointment dates and times mentioned (both offered and confirmed).
Convert dates to YYYY-MM-DD format and times to HH:MM format (24-hour).
Mark status as 'offered' for suggested times, 'confirmed' for accepted ones.

For each appointment, also extract a short event name (less than 5 words) that describes the purpose or type of the meeting.
Examples of event names: "Consultation", "Follow-up Call", "Product Demo", "Support Meeting", "Sales Call", "Technical Review", "Project Discussion", "Team Meeting", "Client Check-in", "Training Session".

{format_instructions}

Be precise and extract only factual information."""
    
    def _calculate_confidence(self, context: str, extracted_data: ExtractedAppointments) -> float:
        confidence_factors = []
        
        if extracted_data.appointments:
            confidence_factors.append(0.4)
        
        context_lower = context.lower()
        time_patterns = ['am', 'pm', 'o\'clock', ':', 'morning', 'afternoon']
        date_patterns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'tomorrow', 'today']
        
        if any(pattern in context_lower for pattern in time_patterns):
            confidence_factors.append(0.3)
        if any(pattern in context_lower for pattern in date_patterns):
            confidence_factors.append(0.3)
        
        return min(sum(confidence_factors), 1.0)
    
    def _manual_parse_response(self, response_content: str) -> ExtractedAppointments:
        try:
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return ExtractedAppointments(**data)
        except:
            pass
        
        return ExtractedAppointments(appointments=[], confidence_score=0.0)
