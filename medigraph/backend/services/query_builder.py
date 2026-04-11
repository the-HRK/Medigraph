"""
Cypher Query Builder Service
Converts structured intent+entities into Neo4j Cypher queries
"""
from typing import List, Optional


class QueryBuilder:
    @staticmethod
    def get_symptoms_of_disease(disease_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease)
        WHERE d.name CONTAINS $disease_name OR $disease_name CONTAINS d.name
              OR toLower(d.name) = toLower($disease_name)
        MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
        RETURN s.id AS id, s.name AS name, s.body_system AS body_system,
               s.type AS type, s.description AS description
        ORDER BY s.body_system, s.name
        """
        return query, {"disease_name": disease_name}

    @staticmethod
    def get_treatments_of_disease(disease_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease)
        WHERE d.name CONTAINS $disease_name OR $disease_name CONTAINS d.name
              OR toLower(d.name) = toLower($disease_name)
        MATCH (d)-[r:TREATED_BY]->(t:Treatment)
        RETURN t.id AS id, t.name AS name, t.type AS type,
               t.category AS category, t.description AS description,
               t.side_effects AS side_effects,
               r.efficacy AS efficacy, r.first_line AS first_line
        ORDER BY r.first_line DESC, t.name
        """
        return query, {"disease_name": disease_name}

    @staticmethod
    def find_diseases_by_symptom(symptom_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        WHERE toLower(s.name) = toLower($symptom_name)
        RETURN d.id AS id, d.name AS name, d.category AS category,
               d.icd_code AS icd_code, d.severity AS severity,
               d.description AS description
        ORDER BY d.severity DESC, d.name
        """
        return query, {"symptom_name": symptom_name}

    @staticmethod
    def get_drug_interactions(drug_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d1:Treatment)-[r:INTERACTS_WITH]->(d2:Treatment)
        WHERE toLower(d1.name) = toLower($drug_name)
        RETURN d2.id AS id, d2.name AS name, d2.type AS type,
               d2.category AS category,
               r.interaction_type AS interaction_type,
               r.severity AS severity,
               r.description AS description
        ORDER BY r.severity DESC, d2.name
        """
        return query, {"drug_name": drug_name}

    @staticmethod
    def check_drug_pair_interaction(drug1_name: str, drug2_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d1:Treatment)-[r:INTERACTS_WITH]->(d2:Treatment)
        WHERE toLower(d1.name) = toLower($drug1_name) AND toLower(d2.name) = toLower($drug2_name)
        RETURN r.interaction_type AS interaction_type,
               r.severity AS severity,
               r.description AS description
        UNION
        MATCH (d1:Treatment)-[r:INTERACTS_WITH]->(d2:Treatment)
        WHERE toLower(d1.name) = toLower($drug2_name) AND toLower(d2.name) = toLower($drug1_name)
        RETURN r.interaction_type AS interaction_type,
               r.severity AS severity,
               r.description AS description
        """
        return query, {"drug1_name": drug1_name, "drug2_name": drug2_name}

    @staticmethod
    def find_diseases_by_category(category: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease {category: $category})
        RETURN d.id AS id, d.name AS name, d.icd_code AS icd_code,
               d.severity AS severity, d.description AS description
        ORDER BY d.severity DESC, d.name
        """
        return query, {"category": category}

    @staticmethod
    def get_related_diseases(disease_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d1:Disease)-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(d2:Disease)
        WHERE (toLower(d1.name) = toLower($disease_name) OR $disease_name CONTAINS d1.name)
          AND d1 <> d2 AND d1.category = d2.category
        WITH d2, count(s) AS shared_symptoms, collect(s.name) AS symptom_list
        RETURN d2.id AS id, d2.name AS name, d2.category AS category,
               d2.severity AS severity, shared_symptoms,
               symptom_list[0..5] AS shared_symptom_names
        ORDER BY shared_symptoms DESC
        LIMIT 10
        """
        return query, {"disease_name": disease_name}

    @staticmethod
    def get_disease_info(disease_name: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease)
        WHERE d.name CONTAINS $disease_name OR $disease_name CONTAINS d.name
              OR toLower(d.name) = toLower($disease_name)
        OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(t:Treatment)
        RETURN d.id AS id, d.name AS name, d.category AS category,
               d.icd_code AS icd_code, d.severity AS severity,
               d.description AS description,
               collect(DISTINCT s.name) AS symptoms,
               collect(DISTINCT t.name) AS treatments
        """
        return query, {"disease_name": disease_name}

    @staticmethod
    def get_drugs_by_category(drug_category: str) -> tuple[str, dict]:
        query = """
        MATCH (t:Treatment {type: 'drug', category: $drug_category})
        RETURN t.id AS id, t.name AS name, t.side_effects AS side_effects
        ORDER BY t.name
        """
        return query, {"drug_category": drug_category}

    @staticmethod
    def find_drugs_treating_symptom(symptom_name: str) -> tuple[str, dict]:
        query = """
        MATCH (t:Treatment)-[:TREATED_BY]->(d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: $symptom_name})
        WHERE t.type = 'drug'
        WITH t, count(DISTINCT d) AS disease_count
        RETURN t.id AS id, t.name AS name, t.side_effects AS side_effects,
               disease_count AS treats_count
        ORDER BY disease_count DESC
        """
        return query, {"symptom_name": symptom_name}

    @staticmethod
    def predict_diseases_by_symptoms(symptoms: List[str]) -> tuple[str, dict]:
        """
        Find diseases matching multiple symptoms, ranked by match count.
        Uses case-insensitive matching.
        """
        symptoms_lower = [s.lower().strip() for s in symptoms]
        query = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        WHERE toLower(s.name) IN $symptoms
        WITH d, collect(toLower(s.name)) AS matched_symptoms
        WHERE size(matched_symptoms) >= 1
        RETURN d.id AS id, d.name AS name, d.category AS category,
               d.severity AS severity,
               size(matched_symptoms) AS match_count,
               matched_symptoms
        ORDER BY match_count DESC, d.severity DESC
        LIMIT 10
        """
        return query, {"symptoms": symptoms_lower}

    @staticmethod
    def get_all_diseases(limit: int = 50, offset: int = 0) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease)
        RETURN d.id AS id, d.name AS name, d.category AS category,
               d.icd_code AS icd_code, d.severity AS severity
        ORDER BY d.name
        SKIP $offset
        LIMIT $limit
        """
        return query, {"limit": limit, "offset": offset}

    @staticmethod
    def get_all_symptoms() -> tuple[str, dict]:
        query = """
        MATCH (s:Symptom)
        RETURN s.id AS id, s.name AS name, s.body_system AS body_system,
               s.type AS type, s.description AS description
        ORDER BY s.body_system, s.name
        """
        return query, {}

    @staticmethod
    def get_all_drugs() -> tuple[str, dict]:
        query = """
        MATCH (t:Treatment {type: 'drug'})
        RETURN t.id AS id, t.name AS name, t.category AS category,
               t.side_effects AS side_effects
        ORDER BY t.name
        """
        return query, {}

    @staticmethod
    def search_entities(search_term: str) -> tuple[str, dict]:
        query = """
        MATCH (d:Disease) WHERE toLower(d.name) CONTAINS toLower($search_term)
        RETURN 'Disease' AS entity_type, d.id AS id, d.name AS name, d.category AS category
        UNION ALL
        MATCH (s:Symptom) WHERE toLower(s.name) CONTAINS toLower($search_term)
        RETURN 'Symptom' AS entity_type, s.id AS id, s.name AS name, s.body_system AS category
        UNION ALL
        MATCH (t:Treatment) WHERE toLower(t.name) CONTAINS toLower($search_term)
        RETURN 'Treatment' AS entity_type, t.id AS id, t.name AS name, t.category AS category
        ORDER BY entity_type, name
        LIMIT 20
        """
        return query, {"search_term": search_term}
