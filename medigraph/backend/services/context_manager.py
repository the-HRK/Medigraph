"""
Context Manager for Chatbot
Handles conversation context and follow-up questions
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationContext:
    """Stores the context of a conversation."""
    last_disease: Optional[str] = None
    last_symptoms: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None
    last_results: Optional[Dict[str, Any]] = None
    conversation_turns: int = 0
    topics_discussed: List[str] = field(default_factory=list)

    def update(self, intent: str, disease: Optional[str] = None,
               symptoms: Optional[List[str]] = None, results: Optional[Dict] = None):
        """Update context with new information."""
        self.conversation_turns += 1
        self.last_intent = intent

        if disease:
            self.last_disease = disease
            if disease not in self.topics_discussed:
                self.topics_discussed.append(disease)

        if symptoms:
            self.last_symptoms = symptoms

        if results:
            self.last_results = results

    def resolve_pronoun(self, text: str) -> str:
        """Resolve 'it', 'they', 'these' to actual entities."""
        text_lower = text.lower()

        # Handle "it" / "this disease" / "that"
        if any(word in text_lower for word in ["it", "this disease", "that"]):
            if self.last_disease:
                # Don't replace if user is asking a new question
                if "what" not in text_lower and "how" not in text_lower:
                    return text

        # Handle "the symptoms" / "these symptoms"
        if any(word in text_lower for word in ["these symptoms", "the symptoms"]):
            if self.last_symptoms:
                return text

        return text

    def can_use_context(self, query: str) -> bool:
        """Check if query can benefit from context (follow-up question)."""
        query_lower = query.lower()

        # Follow-up indicators
        follow_up_words = ["it", "its", "they", "them", "their",
                          "this", "that", "these", "how", "what",
                          "treat", "treated", "cure", "help", "medication"]

        # Check if it's likely a follow-up
        words = query_lower.split()
        if any(word in follow_up_words for word in words):
            return self.conversation_turns > 0

        return False

    def get_follow_up_context(self) -> Dict[str, Any]:
        """Get context data for resolving follow-up questions."""
        return {
            "last_disease": self.last_disease,
            "last_symptoms": self.last_symptoms,
            "last_intent": self.last_intent,
            "topics_discussed": self.topics_discussed[-3:]  # Last 3 topics
        }

    def clear(self):
        """Clear context for new conversation."""
        self.last_disease = None
        self.last_symptoms = []
        self.last_intent = None
        self.last_results = None
        self.conversation_turns = 0


class ContextManager:
    """Manages conversation contexts with session storage."""

    def __init__(self):
        self._contexts: Dict[str, ConversationContext] = {}
        self._session_timeout = 1800  # 30 minutes

    def get_context(self, session_id: str = "default") -> ConversationContext:
        """Get or create context for a session."""
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext()
        return self._contexts[session_id]

    def clear_context(self, session_id: str = "default"):
        """Clear context for a session."""
        if session_id in self._contexts:
            self._contexts[session_id].clear()

    def update_context(self, session_id: str, intent: str,
                      disease: Optional[str] = None,
                      symptoms: Optional[List[str]] = None,
                      results: Optional[Dict] = None):
        """Update context for a session."""
        context = self.get_context(session_id)
        context.update(intent, disease, symptoms, results)

    def enrich_query(self, query: str, session_id: str = "default") -> str:
        """Enrich query with context if it's a follow-up."""
        context = self.get_context(session_id)

        if not context.can_use_context(query):
            return query

        # Resolve pronouns and references
        enriched_query = context.resolve_pronoun(query)

        # For very short queries, use context
        if len(query.split()) <= 4 and context.last_disease:
            # User likely asking follow-up about last disease
            return query

        return enriched_query


# Global instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
