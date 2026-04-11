// ============================================================
// Medigraph - Example Cypher Queries
// ============================================================

// ----------------------------------------------------------
// 1. Get all symptoms of a specific disease
// ----------------------------------------------------------
MATCH (d:Disease {name: 'Hypertension'})-[:HAS_SYMPTOM]->(s:Symptom)
RETURN s.name AS Symptom, s.body_system AS BodySystem;


// ----------------------------------------------------------
// 2. Get all treatments and drugs for a disease
// ----------------------------------------------------------
MATCH (d:Disease {name: 'Type 2 Diabetes'})-[:TREATED_BY]->(t:Treatment)
RETURN t.name AS Treatment, t.type AS Type, t.category AS Category;


// ----------------------------------------------------------
// 3. Find diseases by symptom
// ----------------------------------------------------------
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: 'Chest Pain'})
RETURN d.name AS Disease, d.category AS Category, d.severity AS Severity
ORDER BY d.severity;


// ----------------------------------------------------------
// 4. Get drug interactions for a specific drug
// ----------------------------------------------------------
MATCH (d1:Treatment {name: 'Warfarin'})-[r:INTERACTS_WITH]->(d2:Treatment)
RETURN d2.name AS InteractingDrug, r.interaction_type AS Type, r.severity AS Severity;


// ----------------------------------------------------------
// 5. Find all diseases in a category with severity
// ----------------------------------------------------------
MATCH (d:Disease {category: 'Cardiovascular', severity: 'severe'})
RETURN d.name AS Disease, d.icd_code AS ICDCode
LIMIT 20;


// ----------------------------------------------------------
// 6. Get the most common symptoms across all diseases
// ----------------------------------------------------------
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
RETURN s.name AS Symptom, count(d) AS Frequency
ORDER BY Frequency DESC
LIMIT 10;


// ----------------------------------------------------------
// 7. Find diseases treated by a specific drug class
// ----------------------------------------------------------
MATCH (d:Disease)-[:TREATED_BY]->(t:Treatment {type: 'drug', category: 'ACE Inhibitors'})
RETURN d.name AS Disease, d.category AS Category, t.name AS Drug;


// ----------------------------------------------------------
// 8. Find related diseases sharing symptoms
// ----------------------------------------------------------
MATCH (d1:Disease)-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(d2:Disease)
WHERE d1 <> d2 AND d1.category = d2.category
RETURN d1.name AS Disease1, d2.name AS Disease2, collect(s.name) AS SharedSymptoms
LIMIT 10;


// ----------------------------------------------------------
// 9. Find all drugs that treat multiple diseases
// ----------------------------------------------------------
MATCH (d:Disease)-[r:TREATED_BY]->(t:Treatment {type: 'drug'})
WITH t, count(d) AS diseaseCount, collect(d.name) AS diseases
WHERE diseaseCount >= 5
RETURN t.name AS Drug, diseaseCount AS Treats, diseases[0..3] AS SampleDiseases
ORDER BY diseaseCount DESC;


// ----------------------------------------------------------
// 10. Drug interaction severity analysis
// ----------------------------------------------------------
MATCH (d1:Treatment {type: 'drug'})-[r:INTERACTS_WITH]->(d2:Treatment)
RETURN r.severity AS Severity, count(*) AS Count
ORDER BY Count DESC;


// ----------------------------------------------------------
// 11. Find diseases by body system via symptoms
// ----------------------------------------------------------
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {body_system: 'Neurological'})
RETURN d.category AS Category, count(DISTINCT d) AS DiseaseCount
ORDER BY DiseaseCount DESC;


// ----------------------------------------------------------
// 12. First-line vs second-line treatments analysis
// ----------------------------------------------------------
MATCH (d:Disease)-[r:TREATED_BY]->(t:Treatment)
RETURN t.name AS Treatment,
       count(CASE WHEN r.first_line = 'true' THEN 1 END) AS FirstLine,
       count(CASE WHEN r.first_line = 'false' THEN 1 END) AS SecondLine
ORDER BY FirstLine DESC
LIMIT 15;


// ----------------------------------------------------------
// 13. Find diseases with most symptoms (complex cases)
// ----------------------------------------------------------
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
WITH d, count(s) AS symptomCount
WHERE symptomCount >= 5
RETURN d.name AS Disease, d.category AS Category, symptomCount AS Symptoms
ORDER BY symptomCount DESC
LIMIT 10;


// ----------------------------------------------------------
// 14. Symptom to disease path (reverse lookup)
// ----------------------------------------------------------
MATCH (s:Symptom {name: 'Fatigue'})<-[:CAUSED_BY]-(d:Disease)
RETURN d.name AS Disease, d.severity AS Severity
LIMIT 20;


// ----------------------------------------------------------
// 15. Treatment efficacy by disease category
// ----------------------------------------------------------
MATCH (d:Disease)-[r:TREATED_BY]->(t:Treatment)
RETURN d.category AS Category,
       r.efficacy AS Efficacy,
       count(*) AS Count
ORDER BY Category, Efficacy;
