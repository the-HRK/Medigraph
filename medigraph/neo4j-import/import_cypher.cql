// ============================================================
// Medigraph - Neo4j Import Script
// Run this after starting Neo4j and creating constraints
// ============================================================

// ----------------------------------------------------------
// STEP 1: Clear existing data (OPTIONAL - only for fresh start)
// ----------------------------------------------------------
// MATCH (n) DETACH DELETE n;

// ----------------------------------------------------------
// STEP 2: Load Diseases
// ----------------------------------------------------------
LOAD CSV WITH HEADERS FROM 'file:///diseases.csv' AS row
CREATE (d:Disease {
    id: row.id,
    name: row.name,
    category: row.category,
    icd_code: row.icd_code,
    description: row.description,
    severity: row.severity
});

PRINT 'Diseases loaded: ' + count({(d:Disease)});

// ----------------------------------------------------------
// STEP 3: Load Symptoms
// ----------------------------------------------------------
LOAD CSV WITH HEADERS FROM 'file:///symptoms.csv' AS row
CREATE (s:Symptom {
    id: row.id,
    name: row.name,
    body_system: row.body_system,
    type: row.type,
    description: row.description
});

PRINT 'Symptoms loaded: ' + count({(s:Symptom)});

// ----------------------------------------------------------
// STEP 4: Load Treatments and Drugs
// ----------------------------------------------------------
LOAD CSV WITH HEADERS FROM 'file:///treatments.csv' AS row
CREATE (t:Treatment {
    id: row.id,
    name: row.name,
    type: row.type,
    category: row.category,
    description: row.description,
    side_effects: row.side_effects
});

PRINT 'Treatments/Drugs loaded: ' + count({(t:Treatment)});

// ----------------------------------------------------------
// STEP 5: Load Relationships
// ----------------------------------------------------------

// HAS_SYMPTOM (Disease -> Symptom)
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (d:Disease {id: row.source_id})
MATCH (s:Symptom {id: row.target_id})
WHERE row.type = 'HAS_SYMPTOM'
CREATE (d)-[r:HAS_SYMPTOM {
    severity: row.severity,
    frequency: row.frequency
}]->(s);

PRINT 'HAS_SYMPTOM relationships created';

// CAUSED_BY (Symptom -> Disease)
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (s:Symptom {id: row.source_id})
MATCH (d:Disease {id: row.target_id})
WHERE row.type = 'CAUSED_BY'
CREATE (s)-[r:CAUSED_BY]->(d);

PRINT 'CAUSED_BY relationships created';

// TREATED_BY (Disease -> Treatment/Drug)
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (d:Disease {id: row.source_id})
MATCH (t:Treatment {id: row.target_id})
WHERE row.type = 'TREATED_BY'
CREATE (d)-[r:TREATED_BY {
    efficacy: row.efficacy,
    first_line: row.first_line,
    notes: row.notes
}]->(t);

PRINT 'TREATED_BY relationships created';

// INTERACTS_WITH (Drug -> Drug)
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (d1:Treatment {id: row.source_id})
MATCH (d2:Treatment {id: row.target_id})
WHERE row.type = 'INTERACTS_WITH'
CREATE (d1)-[r:INTERACTS_WITH {
    interaction_type: row.interaction_type,
    severity: row.severity,
    description: row.description
}]->(d2);

PRINT 'INTERACTS_WITH relationships created';

// ----------------------------------------------------------
// STEP 6: Create Graph Context (optional visualization)
// ----------------------------------------------------------
// MATCH (n) RETURN n LIMIT 100;
