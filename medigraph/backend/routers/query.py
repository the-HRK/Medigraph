"""
Query Router - Natural language to Cypher
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from database.connection import get_db
from services.query_service import get_query_service
from services.nlp_processor import NLPProcessor, Intent

router = APIRouter(prefix="/query", tags=["Query"])


class QueryRequest(BaseModel):
    query: str
    intent: Optional[str] = None  # Force specific intent


class QueryResponse(BaseModel):
    intent: str
    query: str
    data: Any
    success: bool


@router.post("/", response_model=QueryResponse)
async def natural_query(request: QueryRequest):
    """
    Process natural language medical query.
    Converts to Cypher, executes against Neo4j, returns structured results.
    """
    db = get_db()
    service = get_query_service(db)

    try:
        result = service.natural_query(request.query)

        if "error" in result and "hint" not in result:
            return QueryResponse(
                intent=result.get("intent", "unknown"),
                query=request.query,
                data=result,
                success=False
            )

        return QueryResponse(
            intent=result.get("intent", "unknown"),
            query=request.query,
            data=result,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents")
async def list_intents():
    """List all supported intents."""
    return {
        "intents": [i.value for i in Intent],
        "examples": {
            "get_symptoms": "What are symptoms of diabetes?",
            "get_treatments": "How is hypertension treated?",
            "find_diseases": "What diseases cause chest pain?",
            "drug_interactions": "Does warfarin interact with aspirin?",
            "predict_disease": "Patient has fatigue and weight loss",
            "get_info": "Tell me about Alzheimer's disease",
            "find_related": "Find diseases similar to Parkinson's",
            "search": "Search for anything"
        }
    }
