"""
Graph Router - Graph data for visualization
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.connection import get_db
from services.query_builder import QueryBuilder

router = APIRouter(prefix="/graph", tags=["Graph"])


class Node(BaseModel):
    id: str
    label: str
    type: str
    properties: dict


class Edge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict


class GraphData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


@router.get("/disease/{disease_name}")
async def get_disease_graph(disease_name: str):
    """
    Get graph data for a specific disease.
    Includes symptoms, treatments, and related diseases.
    """
    db = get_db()
    qb = QueryBuilder()

    try:
        # Get disease with symptoms and treatments
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(t:Treatment)
        RETURN d, collect(DISTINCT s) AS symptoms, collect(DISTINCT t) AS treatments
        """
        results = db.execute_query(query, {"name": disease_name})

        if not results:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        record = results[0]
        disease = record["d"]
        symptoms = record["symptoms"] or []
        treatments = record["treatments"] or []

        nodes = []
        edges = []

        # Disease node
        nodes.append(Node(
            id=disease["id"],
            label=disease["name"],
            type="Disease",
            properties=dict(disease)
        ))

        # Symptom nodes
        for s in symptoms:
            nodes.append(Node(
                id=s["id"],
                label=s["name"],
                type="Symptom",
                properties=dict(s)
            ))
            edges.append(Edge(
                source=disease["id"],
                target=s["id"],
                type="HAS_SYMPTOM",
                properties={}
            ))

        # Treatment nodes
        for t in treatments:
            nodes.append(Node(
                id=t["id"],
                label=t["name"],
                type="Treatment",
                properties=dict(t)
            ))
            edges.append(Edge(
                source=disease["id"],
                target=t["id"],
                type="TREATED_BY",
                properties={}
            ))

        return GraphData(nodes=nodes, edges=edges)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explore")
async def explore_graph(limit: int = 50):
    """
    Get a sample of the graph for visualization.
    Returns random diseases and their connections.
    """
    db = get_db()

    try:
        query = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        WITH d, collect(s.name) AS symptoms
        MATCH (d)-[:TREATED_BY]->(t:Treatment)
        WITH d, symptoms, collect(t.name) AS treatments
        RETURN d.id AS id, d.name AS name, d.category AS category,
               symptoms, treatments
        LIMIT $limit
        """
        results = db.execute_query(query, {"limit": limit})

        nodes = []
        edges = []
        node_ids = set()

        for record in results:
            d = record
            if d["id"] not in node_ids:
                node_ids.add(d["id"])
                nodes.append(Node(
                    id=d["id"],
                    label=d["name"],
                    type="Disease",
                    properties={"category": d["category"]}
                ))

            for sym in (d.get("symptoms") or []):
                sym_id = f"sym_{hash(sym) % 100000}"
                if sym_id not in node_ids:
                    node_ids.add(sym_id)
                    nodes.append(Node(id=sym_id, label=sym, type="Symptom", properties={}))
                edges.append(Edge(source=d["id"], target=sym_id, type="HAS_SYMPTOM", properties={}))

            for treat in (d.get("treatments") or []):
                treat_id = f"treat_{hash(treat) % 100000}"
                if treat_id not in node_ids:
                    node_ids.add(treat_id)
                    nodes.append(Node(id=treat_id, label=treat, type="Treatment", properties={}))
                edges.append(Edge(source=d["id"], target=treat_id, type="TREATED_BY", properties={}))

        return GraphData(nodes=nodes, edges=edges)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def graph_stats():
    """Get graph statistics."""
    db = get_db()

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
