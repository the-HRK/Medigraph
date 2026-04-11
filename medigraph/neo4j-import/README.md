# Medigraph - Healthcare Knowledge Graph

## Overview

Medigraph is a healthcare knowledge graph built on Neo4j that models the relationships between diseases, symptoms, treatments, and drugs.

## Quick Start

### 1. Generate Dataset
```bash
python generate_dataset.py
```

### 2. Neo4j Setup

**Copy CSV files** to your Neo4j import directory:
- Windows: `%APPDATA%\Neo4j\Community\import\`
- Linux: `/var/lib/neo4j/import/`
- macOS: `~/Library/Application Support/Neo4j/Community/import/`

**Run in Neo4j Browser:**
```
:source constraints_indexes.cql
:source import_cypher.cql
```

### 3. Verify
```cypher
MATCH (d:Disease) RETURN count(d) AS DiseaseCount;
MATCH (s:Symptom) RETURN count(s) AS SymptomCount;
MATCH (t:Treatment) RETURN count(t) AS TreatmentCount;
```

## Data Model

```
[Disease] --HAS_SYMPTOM--> [Symptom]
[Disease] --TREATED_BY--> [Treatment/Drug]
[Drug] ----INTERACTS_WITH-> [Drug]
[Symptom] --CAUSED_BY----> [Disease]
```

## File Structure

| File | Description |
|------|-------------|
| `SCHEMA.md` | Complete schema documentation |
| `constraints_indexes.cql` | Neo4j constraints and indexes |
| `import_cypher.cql` | Data import queries |
| `example_queries.cql` | 15 example Cypher queries |
| `generate_dataset.py` | Python data generator |
| `data/diseases.csv` | 1,013 diseases |
| `data/symptoms.csv` | 49 symptoms |
| `data/treatments.csv` | 117 drugs/treatments |
| `data/relationships.csv` | 11,329 relationships |

## Sample Queries

```cypher
// Get symptoms for a disease
MATCH (d:Disease {name: 'Hypertension'})-[:HAS_SYMPTOM]->(s:Symptom)
RETURN s.name;

// Find diseases by symptom
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: 'Chest Pain'})
RETURN d.name, d.severity;

// Get drug interactions
MATCH (d1:Treatment {name: 'Warfarin'})-[r:INTERACTS_WITH]->(d2)
RETURN d2.name, r.severity;

// Find related diseases
MATCH (d1)-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(d2)
WHERE d1.category = d2.category AND d1 <> d2
RETURN d1.name, d2.name, collect(s.name) LIMIT 10;
```
