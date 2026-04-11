# Medigraph Backend

FastAPI backend for the Medigraph Healthcare Knowledge Graph API.

## Features

- **Natural Language Queries**: Convert medical questions to Cypher queries
- **Intent Detection**: Identifies query type (symptoms, treatments, drug interactions, etc.)
- **Entity Extraction**: Extracts diseases, symptoms, and drugs from queries
- **Disease Prediction**: Predicts diseases based on multiple symptoms
- **Drug Interaction Checker**: Checks interactions between two drugs
- **Graph Data API**: Provides graph visualization data

## Prerequisites

- Python 3.10+
- Neo4j 5.x (running locally or remote)
- Generated dataset (see `../neo4j-import/`)

## Installation

1. **Create virtual environment**:
```bash
cd medigraph/backend
python -m venv venv

venv\Scripts\activate  # Windows
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

4. **Set up Neo4j database**:
```bash
# Run the import scripts from ../neo4j-import/
# Follow the README.md there first
```

5. **Run the server**:
```bash
uvicorn main:app --reload --port 8000
```

Or with Python:
```bash
python main.py
```

## API Endpoints

### Query Endpoint
```
POST /query/
```
Process natural language medical queries.

**Example**:
```json
{
  "query": "What are the symptoms of diabetes?"
}
```

**Response**:
```json
{
  "intent": "get_symptoms",
  "query": "What are the symptoms of diabetes?",
  "data": {
    "disease": "Diabetes",
    "symptoms": [...],
    "count": 6
  },
  "success": true
}
```

### Chat Endpoint
```
POST /chat/
```
Conversational interface with natural language responses.

**Example**:
```json
{
  "message": "What are symptoms of hypertension?"
}
```

### Graph Endpoint
```
GET /graph/disease/{disease_name}
GET /graph/explore
GET /graph/stats
```

### Supported Intent Types

| Intent | Example Query |
|--------|---------------|
| `get_symptoms` | "What are symptoms of diabetes?" |
| `get_treatments` | "How is hypertension treated?" |
| `find_diseases` | "What diseases cause chest pain?" |
| `drug_interactions` | "Does warfarin interact with aspirin?" |
| `predict_disease` | "Patient has fatigue and weight loss" |
| `get_info` | "Tell me about Alzheimer's disease" |
| `find_related` | "Find diseases similar to Parkinson's" |
| `search` | "Search for anything" |

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── database/
│   ├── __init__.py
│   └── connection.py       # Neo4j connection management
├── routers/
│   ├── __init__.py
│   ├── query.py           # /query endpoint
│   ├── chat.py            # /chat endpoint
│   └── graph.py           # /graph endpoint
├── services/
│   ├── __init__.py
│   ├── nlp_processor.py   # Intent detection & entity extraction
│   ├── query_builder.py   # Cypher query generation
│   └── query_service.py   # Query execution service
└── utils/
    ├── __init__.py
    ├── helpers.py         # Common utilities
    └── validators.py      # Input validation
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `DEBUG` | `true` | Debug mode |

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Error Handling

The API returns structured error responses:

```json
{
  "intent": "unknown",
  "query": "invalid query",
  "data": {
    "error": "Could not understand query",
    "original_query": "invalid query",
    "hint": "Try asking: 'What are symptoms of diabetes?'"
  },
  "success": false
}
```

## Development

### Running Tests
```bash
# Coming soon
pytest tests/
```

### Code Style
```bash
ruff format .
ruff check .
```
