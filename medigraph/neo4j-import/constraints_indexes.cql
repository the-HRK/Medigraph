// ============================================================
// Medigraph - Constraints and Indexes
// Run these BEFORE importing data
// ============================================================

// ----------------------------------------------------------
// CONSTRAINTS - Ensure data integrity
// ----------------------------------------------------------

// Disease constraints
CREATE CONSTRAINT disease_id IF NOT EXISTS
FOR (d:Disease) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT disease_name IF NOT EXISTS
FOR (d:Disease) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT disease_icd IF NOT EXISTS
FOR (d:Disease) REQUIRE d.icd_code IS UNIQUE;

// Symptom constraints
CREATE CONSTRAINT symptom_id IF NOT EXISTS
FOR (s:Symptom) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT symptom_name IF NOT EXISTS
FOR (s:Symptom) REQUIRE s.name IS UNIQUE;

// Treatment/Drug constraints
CREATE CONSTRAINT treatment_id IF NOT EXISTS
FOR (t:Treatment) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT treatment_name IF NOT EXISTS
FOR (t:Treatment) REQUIRE t.name IS UNIQUE;

// ----------------------------------------------------------
// INDEXES - Speed up queries
// ----------------------------------------------------------

// Disease indexes
CREATE INDEX disease_category IF NOT EXISTS
FOR (d:Disease) ON (d.category);

CREATE INDEX disease_severity IF NOT EXISTS
FOR (d:Disease) ON (d.severity);

// Symptom indexes
CREATE INDEX symptom_body_system IF NOT EXISTS
FOR (s:Symptom) ON (s.body_system);

// Treatment indexes
CREATE INDEX treatment_type IF NOT EXISTS
FOR (t:Treatment) ON (t.type);

CREATE INDEX treatment_category IF NOT EXISTS
FOR (t:Treatment) ON (t.category);

// Relationship indexes
CREATE INDEX has_symptom_severity IF NOT EXISTS
FOR ()-[r:HAS_SYMPTOM]-() ON (r.severity);

CREATE INDEX treated_by_efficacy IF NOT EXISTS
FOR ()-[r:TREATED_BY]-() ON (r.efficacy);

// ----------------------------------------------------------
// Verify constraints and indexes
// ----------------------------------------------------------
SHOW CONSTRAINTS;
SHOW INDEXES;
