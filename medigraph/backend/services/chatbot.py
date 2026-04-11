"""
Chatbot Service
Main chatbot logic that orchestrates context, queries, and responses
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from services.context_manager import ContextManager, get_context_manager
from services.response_generator import ResponseGenerator, get_response_generator
from services.query_service import QueryService, get_query_service
from services.nlp_processor import Intent, NLPProcessor, get_nlp_processor
from services.llm_service import LLMService, get_llm_service
from database.connection import Neo4jConnection


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "user" or "bot"
    content: str
    intent: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class ChatResponse:
    """Represents a complete chatbot response."""
    response: str
    intent: str
    confidence: float
    confidence_label: str
    explanation: str
    suggestions: List[str]
    data: Dict[str, Any]
    context_used: bool
    llm_enhanced: bool = False  # Whether LLM was used to enhance response


class Chatbot:
    """
    Main chatbot service for Medigraph.

    Orchestrates:
    - Context management (follow-up questions)
    - NLP processing (intent detection)
    - Query execution (database queries)
    - Response generation (natural language)
    - Optional LLM enhancement
    """

    def __init__(self, db: Neo4jConnection):
        self.db = db
        self.query_service = get_query_service(db)
        self.nlp = get_nlp_processor()
        self.response_gen = get_response_generator()
        self.context_mgr = get_context_manager()
        self.llm_service = get_llm_service()

    def process(self, message: str, session_id: str = "default") -> ChatResponse:
        """
        Process a user message and return a complete response.

        Steps:
        1. Enrich query with context (if follow-up)
        2. Parse intent and entities
        3. Execute query against database
        4. Generate natural language response
        5. Optionally enhance with LLM
        6. Update context
        """
        # Step 1: Enrich query with context
        enriched_message = self.context_mgr.enrich_query(message, session_id)

        # Step 2: Parse intent
        parsed = self.nlp.parse(enriched_message)

        # Step 3: Execute query
        result = self.query_service.execute_intent(parsed.intent, parsed.entities)

        # Step 4: Get context for response generation
        context = self.context_mgr.get_context(session_id)

        # Step 5: Generate response (template-based)
        response_data = self.response_gen.generate_response(
            parsed.intent.value,
            result,
            context
        )

        # Step 6: Optionally enhance with LLM
        if self.llm_service.is_enabled():
            llm_response = self.llm_service.enhance_response(
                graph_data=result,
                original_response=response_data["response"],
                intent=parsed.intent.value,
                context=context.get_follow_up_context() if context else None
            )
            response_data["response"] = llm_response.enhanced_text
            response_data["confidence"] = min(1.0, response_data["confidence"] + llm_response.confidence_modifier)
            response_data["llm_enhanced"] = True
            response_data["llm_sources"] = llm_response.sources_used
        else:
            response_data["llm_enhanced"] = False

        # Step 7: Update context
        self._update_context(session_id, parsed.intent.value, result)

        # Step 8: Build final response
        return ChatResponse(
            response=response_data["response"],
            intent=response_data["intent"],
            confidence=response_data["confidence"],
            confidence_label=response_data["confidence_label"],
            explanation=response_data["explanation"],
            suggestions=response_data["suggestions"],
            data=response_data["data"],
            context_used=session_id in self.context_mgr._contexts and
                        self.context_mgr._contexts[session_id].conversation_turns > 0
        )

    def _update_context(self, session_id: str, intent: str, result: Dict[str, Any]):
        """Update conversation context after processing a message."""
        disease = None
        symptoms = []

        # Extract disease
        if "disease" in result:
            disease = result["disease"]
        elif "disease" in result.get("data", {}):
            disease = result["data"]["disease"]

        # Extract symptoms
        if "symptoms" in result:
            symptoms = [s.get("name", "") for s in result.get("symptoms", [])]
        elif "input_symptoms" in result:
            symptoms = result["input_symptoms"]

        # Update context
        self.context_mgr.update_context(
            session_id=session_id,
            intent=intent,
            disease=disease,
            symptoms=symptoms,
            results=result
        )

    def reset_context(self, session_id: str = "default"):
        """Reset conversation context."""
        self.context_mgr.clear_context(session_id)

    def get_context_info(self, session_id: str = "default") -> Dict[str, Any]:
        """Get current context information."""
        context = self.context_mgr.get_context(session_id)
        return {
            "last_disease": context.last_disease,
            "last_symptoms": context.last_symptoms,
            "conversation_turns": context.conversation_turns,
            "topics_discussed": context.topics_discussed
        }


# Global instance cache
_chatbot: Optional[Chatbot] = None


def get_chatbot(db: Neo4jConnection) -> Chatbot:
    """Get or create chatbot instance."""
    global _chatbot
    if _chatbot is None:
        _chatbot = Chatbot(db)
    return _chatbot


def reset_chatbot():
    """Reset chatbot instance (for testing)."""
    global _chatbot
    _chatbot = None
