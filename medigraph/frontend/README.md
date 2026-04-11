# Medigraph Frontend

React-based UI for the Medigraph Healthcare Knowledge Graph.

## Features

- **Chat Interface**: Natural language queries with conversational responses
- **Graph Visualization**: Interactive Cytoscape.js knowledge graph
- **Split View**: Chat on the left, graph visualization on the right
- **Real-time Updates**: Graph updates when diseases are selected

## Tech Stack

- React 18
- Vite
- Cytoscape.js
- Axios

## Prerequisites

- Backend server running on http://localhost:8000
- Neo4j database connected

## Installation

```bash
cd medigraph/frontend
npm install
```

## Development

```bash
npm run dev
```

Access at http://localhost:5173

## Build

```bash
npm run build
```

Output in `dist/` directory.

## API Connection

The frontend connects to the backend at `http://localhost:8000`. Update `src/services/api.js` to change the API base URL.

### Endpoints Used

- `POST /query/` - Natural language queries
- `POST /chat/` - Conversational responses
- `GET /graph/disease/{name}` - Graph data for disease
- `GET /graph/stats` - Database statistics
- `GET /health` - Health check
- `GET /stats` - Database stats

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat.jsx      # Chat interface
│   │   ├── Chat.css
│   │   ├── Graph.jsx     # Cytoscape graph
│   │   └── Graph.css
│   ├── services/
│   │   └── api.js        # API client
│   ├── App.jsx           # Main app
│   ├── App.css
│   └── main.jsx          # Entry point
└── index.html
```
