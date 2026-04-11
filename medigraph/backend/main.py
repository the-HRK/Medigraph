"""
Medigraph Backend - FastAPI Application
Healthcare Knowledge Graph Query API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database.connection import get_db, Neo4jConnection
from routers import query, chat, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    # Startup
    db = Neo4jConnection()
    db.connect()
    yield
    # Shutdown
    db.close()


app = FastAPI(
    title="Medigraph API",
    description="Healthcare Knowledge Graph API - Query medical data using natural language",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router)
app.include_router(chat.router)
app.include_router(graph.router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": "Medigraph API",
        "version": "1.0.0",
        "description": "Healthcare Knowledge Graph API",
        "endpoints": {
            "query": "/query - Natural language medical queries",
            "chat": "/chat - Conversational responses",
            "graph": "/graph - Graph visualization data"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    db = Neo4jConnection()
    db.connect()
    is_connected = db.verify_connectivity()
    db.close()

    return {
        "status": "healthy" if is_connected else "degraded",
        "database": "connected" if is_connected else "disconnected"
    }


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get database statistics."""
    db = Neo4jConnection()
    db.connect()

    try:
        query = """
        MATCH (d:Disease) WITH count(d) AS disease_count
        MATCH (s:Symptom) WITH disease_count, count(s) AS symptom_count
        MATCH (t:Treatment) WITH disease_count, symptom_count, count(t) AS treatment_count
        MATCH ()-[r]->() WITH disease_count, symptom_count, treatment_count, count(r) AS relationship_count
        RETURN disease_count, symptom_count, treatment_count, relationship_count
        """
        results = db.execute_query(query)

        if results:
            return results[0]

        return {
            "disease_count": 0,
            "symptom_count": 0,
            "treatment_count": 0,
            "relationship_count": 0
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
