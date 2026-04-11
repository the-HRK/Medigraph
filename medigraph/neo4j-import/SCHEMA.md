# Medigraph Data Layer Specification

## Graph Schema Design

### Node Labels

| Label | Properties | Description |
|-------|-----------|-------------|
| `Disease` | `id`, `name`, `category`, `icd_code`, `description`, `severity` | Medical conditions diagnosed in patients |
| `Symptom` | `id`, `name`, `body_system`, `type`, `description` | Observable signs reported by patients |
| `Treatment` | `id`, `name`, `type`, `category`, `description`, `side_effects` | Both pharmacological (Drug) and procedural interventions |

### Relationship Types

| Type | Start | End | Properties | Description |
|------|-------|-----|-----------|-------------|
| `HAS_SYMPTOM` | Disease | Symptom | `severity`, `frequency` | Links disease to its clinical manifestations |
| `TREATED_BY` | Disease | Treatment | `efficacy`, `first_line`, `notes` | Standard-of-care treatments |
| `CAUSED_BY` | Symptom | Disease | — | Reverse lookup for symptom → disease |
| `INTERACTS_WITH` | Treatment | Treatment | `interaction_type`, `severity`, `description` | Drug-drug interactions |

### Design Decisions

1. **Unified Treatment node**: Both drugs and procedures are `Treatment` nodes with a `type` property — this simplifies traversal and allows same relationship type for all interventions.

2. **Bidirectional Symptom relationship**: `HAS_SYMPTOM` (disease→symptom) and `CAUSED_BY` (symptom→disease) enable efficient bidirectional traversal without duplicating data.

3. **ICD codes on Disease**: Enables integration with real healthcare systems (ICD-10 classification).

4. **Drug interaction properties**: Stores `interaction_type` and `severity` for clinical decision support.

5. **Treatment efficacy tracking**: Supports evidence-based querying and treatment comparison.

6. **Body system on symptoms**: Enables efficient querying by anatomical region.

---

## Dataset Statistics

```
Diseases:       1,013
Symptoms:          49
Drugs:            85
Treatments:       32
Total Nodes:    1,179

Relationships: 11,329
  HAS_SYMPTOM:    4,517
  CAUSED_BY:      4,517
  TREATED_BY:     2,007
  INTERACTS_WITH:   288
```

---

## File Structure

```
medigraph/neo4j-import/
├── SCHEMA.md                 # This file
├── constraints_indexes.cql    # Neo4j constraints & indexes
├── import_cypher.cql         # Data import queries
├── example_queries.cql       # 15 example queries
├── generate_dataset.py       # Python data generator
└── data/
    ├── diseases.csv           # 1,013 disease records
    ├── symptoms.csv           # 49 symptom records
    ├── treatments.csv         # 117 drug/treatment records
    └── relationships.csv      # 11,329 relationship records
```

---

## CSV Format

### diseases.csv
```csv
id,name,category,icd_code,description,severity
DIS_00001,Hypertension,Cardiovascular,I01,A cardiovascular condition.,mild
```

### symptoms.csv
```csv
id,name,body_system,type,description
SYM_001,Chest Pain,Cardiovascular,symptom,A cardiovascular symptom.
```

### treatments.csv
```csv
id,name,type,category,description,side_effects
DRG_0001,Lisinopril,drug,Pharmacological,A medication used in treatment.,Fatigue
TRT_0001,Physical Therapy,treatment,Intervention,A treatment procedure.,
```

### relationships.csv
```csv
source_id,source_type,target_id,target_type,type,severity,frequency,efficacy,first_line,interaction_type,description
DIS_00001,Disease,SYM_010,Symptom,HAS_SYMPTOM,mild,constant,,,,
```

---

## Import Instructions

### Prerequisites
- Neo4j Desktop or Neo4j Server (4.x or 5.x)
- APOC library installed
- Neo4j browser access

### Step 1: Create Constraints and Indexes
Open Neo4j Browser and run:
```
:source constraints_indexes.cql
```

### Step 2: Import Data
Copy the CSV files to Neo4j import directory:
- **Neo4j Desktop**: Place in `import/` folder within your database directory
- **Neo4j Server**: Place in `/var/lib/neo4j/import/` (Linux) or use `dbms.directories.import` path

Then run:
```
:source import_cypher.cql
```

### Step 3: Verify Import
```cypher
MATCH (d:Disease) RETURN count(d) AS DiseaseCount;
MATCH (s:Symptom) RETURN count(s) AS SymptomCount;
MATCH (t:Treatment) RETURN count(t) AS TreatmentCount;
MATCH ()-[r]->() RETURN count(r) AS RelationshipCount;
```

---

## Example Query Results

### Diseases by Symptom
```cypher
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: 'Chest Pain'})
RETURN d.category, count(d) AS count ORDER BY count DESC
```
Finds all disease categories that present with chest pain.

### Drug Interaction Count
```cypher
MATCH (d:Treatment {type:'drug'})-[r:INTERACTS_WITH]->()
RETURN d.name, count(r) AS interactions ORDER BY interactions DESC LIMIT 5
```
Identifies drugs with most interactions (risk assessment).

### Disease Network by Category
```cypher
MATCH (d:Disease {category:'Neurological'})-[:HAS_SYMPTOM]->(s:Symptom)
RETURN s.name, count(d) ORDER BY count DESC LIMIT 10
```
Most frequent neurological symptoms.

---

## Scalability Notes

- **Current scale**: ~1,000 diseases, ~11K relationships
- **Design supports**: Millions of nodes and relationships
- **For NLP integration**: ICD codes and body_system properties enable medical NER mapping
- **For real-world use**: Replace generated data with MIMIC-IV, SNOMED-CT, or other clinical datasets
