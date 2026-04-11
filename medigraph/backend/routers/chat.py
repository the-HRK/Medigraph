"""
Chat Router - Enhanced Conversational Interface
Uses the new chatbot service for intelligent responses
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from database.connection import get_db
from services.chatbot import Chatbot, get_chatbot
from services.llm_service import get_llm_service

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    session_id: Optional[str] = "default"


class EnhancedChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    confidence_label: str
    explanation: str
    suggestions: List[str]
    data: Any
    context_used: bool
    llm_enhanced: Optional[bool] = False


@router.post("/", response_model=EnhancedChatResponse)
async def chat(request: ChatMessage):
    """
    Enhanced conversational interface with:
    - Context awareness (follow-up questions)
    - Confidence scoring
    - Explainability
    - Suggestions
    """
    db = get_db()
    chatbot = get_chatbot(db)

    try:
        result = chatbot.process(
            message=request.message,
            session_id=request.session_id or "default"
        )

        return EnhancedChatResponse(
            response=result.response,
            intent=result.intent,
            confidence=result.confidence,
            confidence_label=result.confidence_label,
            explanation=result.explanation,
            suggestions=result.suggestions,
            data=result.data,
            context_used=result.context_used,
            llm_enhanced=result.llm_enhanced
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_chat(session_id: str = "default"):
    """Reset conversation context."""
    db = get_db()
    chatbot = get_chatbot(db)
    chatbot.reset_context(session_id)
    return {"message": "Context reset successfully", "session_id": session_id}


@router.get("/context/{session_id}")
async def get_context(session_id: str = "default"):
    """Get current conversation context."""
    db = get_db()
    chatbot = get_chatbot(db)
    context = chatbot.get_context_info(session_id)
    return context


@router.get("/intents")
async def list_intents():
    """List all supported intents with examples."""
    return {
        "intents": {
            "get_symptoms": {
                "examples": [
                    "What are symptoms of diabetes?",
                    "Tell me about flu symptoms",
                    "What are the signs of hypertension?"
                ]
            },
            "get_treatments": {
                "examples": [
                    "How is diabetes treated?",
                    "What's the treatment for hypertension?",
                    "How to treat the flu?"
                ]
            },
            "find_diseases": {
                "examples": [
                    "What diseases cause chest pain?",
                    "Which diseases have fever as symptom?",
                    "What causes headache and fatigue?"
                ]
            },
            "drug_interactions": {
                "examples": [
                    "Does aspirin interact with warfarin?",
                    "Can I take metformin with lisinopril?",
                    "Drug interactions for ibuprofen"
                ]
            },
            "predict_disease": {
                "examples": [
                    "I have fever and cough, what could it be?",
                    "Patient with fatigue and weight loss",
                    "Symptoms: headache, nausea, dizziness"
                ]
            },
            "get_info": {
                "examples": [
                    "Tell me about Alzheimer's disease",
                    "What is diabetes?",
                    "Information on Parkinson's"
                ]
            },
            "find_related": {
                "examples": [
                    "Find diseases similar to diabetes",
                    "What diseases are related to hypertension?",
                    "Related conditions to asthma"
                ]
            }
        }
    }


@router.get("/example-conversations")
async def get_example_conversations():
    """Get example conversations to demonstrate chatbot capabilities."""
    return {
        "conversations": [
            {
                "title": "Follow-up Questions",
                "turns": [
                    {
                        "user": "What are symptoms of hypertension?",
                        "bot_confidence": "High confidence",
                        "note": "Context: last_disease = Hypertension"
                    },
                    {
                        "user": "How is it treated?",
                        "bot_confidence": "High confidence",
                        "note": "Uses context to understand 'it' = Hypertension"
                    }
                ]
            },
            {
                "title": "Disease Prediction",
                "turns": [
                    {
                        "user": "I have chest pain and shortness of breath",
                        "bot_confidence": "Good confidence",
                        "note": "Predicts diseases matching symptoms"
                    }
                ]
            },
            {
                "title": "Drug Interactions",
                "turns": [
                    {
                        "user": "Does warfarin interact with aspirin?",
                        "bot_confidence": "High confidence",
                        "note": "Returns specific interaction data"
                    }
                ]
            }
        ]
    }


@router.get("/llm-status")
async def get_llm_status():
    """Check if LLM enhancement is available and enabled."""
    llm_service = get_llm_service()
    health = llm_service.check_health()
    return {
        "llm_enabled": llm_service.is_enabled(),
        "provider": llm_service.config.provider.value if llm_service.config else "none",
        "model": llm_service.config.model if llm_service.config else None,
        "health": health
    }
