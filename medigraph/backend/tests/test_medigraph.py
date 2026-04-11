"""
Medigraph Test Suite
Comprehensive testing for data integrity, NLP, queries, and chatbot
"""
import pytest
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Neo4jConnection
from services.nlp_processor import NLPProcessor, Intent
from services.query_service import QueryService
from services.query_builder import QueryBuilder
from services.response_generator import ResponseGenerator
from services.context_manager import ContextManager


@pytest.fixture(scope="module")
def db():
    """Create database connection for tests."""
    db = Neo4jConnection()
    db.connect()
    yield db
    db.close()


@pytest.fixture
def nlp():
    return NLPProcessor()


@pytest.fixture
def query_service(db):
    return QueryService(db)


@pytest.fixture
def response_gen():
    return ResponseGenerator()


@pytest.fixture
def context_mgr():
    return ContextManager()


class TestDataIntegrity:
    """PART 3: Data Integrity Testing"""

    def test_duplicate_disease_nodes(self, db):
        """Detect duplicate Disease nodes (same name but different id)."""
        query = """
        MATCH (d:Disease)
        WITH d.name AS name, collect(d.id) AS ids, count(*) AS cnt
        WHERE cnt > 1
        RETURN name, ids, cnt
        """
        results = db.execute_query(query)
        assert len(results) == 0, f"Duplicate diseases found: {results}"

    def test_missing_disease_properties(self, db):
        """Detect Disease nodes with missing required properties."""
        query = """
        MATCH (d:Disease)
        WHERE d.name IS NULL OR d.name = ''
        RETURN d.id AS id, d.name AS name
        """
        results = db.execute_query(query)
        assert len(results) == 0, f"Diseases with missing name: {results}"

    def test_orphan_symptom_nodes(self, db):
        """Detect Symptom nodes not connected to any Disease."""
        query = """
        MATCH (s:Symptom)
        WHERE NOT exists((s)<-[:HAS_SYMPTOM]-())
        RETURN s.id AS id, s.name AS name
        """
        results = db.execute_query(query)
        # Orphans are acceptable if intentional (symptoms for future diseases)
        print(f"Orphan symptoms: {len(results)}")

    def test_orphan_treatment_nodes(self, db):
        """Detect Treatment nodes not connected to any Disease."""
        query = """
        MATCH (t:Treatment)
        WHERE NOT exists((t)<-[:TREATED_BY]-())
        RETURN t.id AS id, t.name AS name
        """
        results = db.execute_query(query)
        print(f"Orphan treatments: {len(results)}")

    def test_diseases_without_symptoms(self, db):
        """Detect Disease nodes without any symptoms."""
        query = """
        MATCH (d:Disease)
        WHERE NOT exists((d)-[:HAS_SYMPTOM]->())
        RETURN d.id AS id, d.name AS name
        """
        results = db.execute_query(query)
        print(f"Diseases without symptoms: {len(results)}")

    def test_diseases_without_treatments(self, db):
        """Detect Disease nodes without any treatments."""
        query = """
        MATCH (d:Disease)
        WHERE NOT exists((d)-[:TREATED_BY]->())
        RETURN d.id AS id, d.name AS name
        """
        results = db.execute_query(query)
        print(f"Diseases without treatments: {len(results)}")

    def test_bidirectional_relationships(self, db):
        """Check if drug interaction relationships are bidirectional."""
        query = """
        MATCH (t1:Treatment)-[r:INTERACTS_WITH]->(t2:Treatment)
        WHERE NOT exists((t2)-[:INTERACTS_WITH]->(t1))
        RETURN t1.name AS drug1, t2.name AS drug2
        """
        results = db.execute_query(query)
        print(f"Non-bidirectional drug interactions: {len(results)}")

    def test_symptom_body_system_coverage(self, db):
        """Check if symptoms have body_system property."""
        query = """
        MATCH (s:Symptom)
        WHERE s.body_system IS NULL OR s.body_system = ''
        RETURN count(s) AS count
        """
        results = db.execute_query(query)
        count = results[0]["count"] if results else 0
        print(f"Symptoms without body_system: {count}")


class TestNLPProcessing:
    """PART 1 & 2: NLP Evaluation"""

    def test_symptom_intent_detection(self, nlp):
        """Test intent detection for symptom queries."""
        test_cases = [
            ("What are symptoms of diabetes?", Intent.GET_SYMPTOMS),
            ("Tell me about flu symptoms", Intent.GET_SYMPTOMS),
            ("What are the signs of hypertension?", Intent.GET_SYMPTOMS),
        ]
        for query, expected in test_cases:
            result = nlp.parse(query)
            assert result.intent == expected, f"Query '{query}': expected {expected}, got {result.intent}"

    def test_treatment_intent_detection(self, nlp):
        """Test intent detection for treatment queries."""
        test_cases = [
            ("How is diabetes treated?", Intent.GET_TREATMENTS),
            ("What's the treatment for hypertension?", Intent.GET_TREATMENTS),
            ("How to treat the flu?", Intent.GET_TREATMENTS),
        ]
        for query, expected in test_cases:
            result = nlp.parse(query)
            assert result.intent == expected, f"Query '{query}': expected {expected}, got {result.intent}"

    def test_find_diseases_intent(self, nlp):
        """Test intent detection for find diseases queries."""
        test_cases = [
            ("What diseases cause chest pain?", Intent.FIND_DISEASES),
            ("Which diseases have fever as symptom?", Intent.FIND_DISEASES),
        ]
        for query, expected in test_cases:
            result = nlp.parse(query)
            assert result.intent == expected, f"Query '{query}': expected {expected}, got {result.intent}"

    def test_drug_interaction_intent(self, nlp):
        """Test intent detection for drug interaction queries."""
        test_cases = [
            ("Does aspirin interact with warfarin?", Intent.DRUG_INTERACTIONS),
            ("Can I take metformin with lisinopril?", Intent.DRUG_INTERACTIONS),
        ]
        for query, expected in test_cases:
            result = nlp.parse(query)
            assert result.intent == expected, f"Query '{query}': expected {expected}, got {result.intent}"

    def test_predict_disease_intent(self, nlp):
        """Test intent detection for disease prediction."""
        test_cases = [
            ("I have fever and cough, what could it be?", Intent.PREDICT_DISEASE),
            ("Patient with fatigue and weight loss", Intent.PREDICT_DISEASE),
        ]
        for query, expected in test_cases:
            result = nlp.parse(query)
            assert result.intent == expected, f"Query '{query}': expected {expected}, got {result.intent}"

    def test_entity_extraction_diseases(self, nlp):
        """Test entity extraction for diseases."""
        query = "What are symptoms of hypertension?"
        result = nlp.parse(query)
        disease_entities = [e for e in result.entities if e.type == "disease"]
        assert len(disease_entities) >= 1, f"No disease entities extracted from '{query}'"
        assert disease_entities[0].value.lower() == "hypertension", f"Wrong disease: {disease_entities[0].value}"

    def test_entity_extraction_symptoms(self, nlp):
        """Test entity extraction for symptoms."""
        query = "I have fever and cough"
        result = nlp.parse(query)
        symptom_entities = [e for e in result.entities if e.type == "symptom"]
        assert len(symptom_entities) >= 2, f"Not enough symptoms: {symptom_entities}"

    def test_synonym_handling(self, nlp):
        """Test if system handles common medical synonyms."""
        # "high blood sugar" should relate to diabetes
        query = "What is high blood sugar?"
        result = nlp.parse(query)
        # System should at least recognize it as a search or info intent
        assert result.intent != Intent.UNKNOWN or len(result.entities) > 0

    def test_variation_handling(self, nlp):
        """Test query variations."""
        variations = [
            "treatment for flu",
            "how to treat flu",
            "how is flu treated",
            "flu treatment"
        ]
        results = [nlp.parse(v).intent for v in variations]
        # Most should map to get_treatments
        get_treatments_count = sum(1 for r in results if r == Intent.GET_TREATMENTS)
        assert get_treatments_count >= 3, f"Not enough variations mapped correctly: {results}"

    def test_unknown_query(self, nlp):
        """Test graceful handling of unknown queries."""
        query = "asdfghjkl query"
        result = nlp.parse(query)
        # Should not crash, intent might be UNKNOWN or SEARCH
        assert result is not None

    def test_empty_query(self, nlp):
        """Test empty query handling."""
        query = ""
        result = nlp.parse(query)
        assert result is not None


class TestQueryExecution:
    """Test Cypher queries directly."""

    def test_get_symptoms_query(self, db):
        """Test symptoms of disease query."""
        query = """
        MATCH (d:Disease {name: 'Hypertension'})-[:HAS_SYMPTOM]->(s:Symptom)
        RETURN s.name AS name
        LIMIT 5
        """
        results = db.execute_query(query)
        assert len(results) > 0, "No symptoms found for Hypertension"
        print(f"Hypertension symptoms: {[r['name'] for r in results]}")

    def test_get_treatments_query(self, db):
        """Test treatments of disease query."""
        query = """
        MATCH (d:Disease {name: 'Hypertension'})-[r:TREATED_BY]->(t:Treatment)
        RETURN t.name AS name, r.efficacy AS efficacy
        """
        results = db.execute_query(query)
        assert len(results) > 0, "No treatments found for Hypertension"
        print(f"Hypertension treatments: {[r['name'] for r in results]}")

    def test_disease_by_symptom_query(self, db):
        """Test find diseases by symptom query."""
        query = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: 'Fever'})
        RETURN d.name AS name
        LIMIT 5
        """
        results = db.execute_query(query)
        print(f"Diseases with Fever: {[r['name'] for r in results]}")

    def test_drug_interaction_query(self, db):
        """Test drug interaction query."""
        query = """
        MATCH (t1:Treatment {name: 'Aspirin'})-[r:INTERACTS_WITH]->(t2:Treatment {name: 'Warfarin'})
        RETURN r.interaction_type AS type, r.severity AS severity
        """
        results = db.execute_query(query)
        print(f"Aspirin-Warfarin interaction: {results}")

    def test_predict_disease_query(self, db):
        """Test disease prediction query."""
        query = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        WHERE s.name IN ['Chest pain', 'Shortness of breath']
        WITH d, count(s) AS match_count
        RETURN d.name AS name, match_count
        ORDER BY match_count DESC
        LIMIT 5
        """
        results = db.execute_query(query)
        print(f"Predicted diseases: {results}")


class TestQueryService:
    """Test QueryService integration."""

    def test_service_get_symptoms(self, query_service):
        """Test query service for symptoms."""
        result = query_service.execute_intent(
            Intent.GET_SYMPTOMS,
            [{"type": "disease", "value": "Hypertension", "original": "Hypertension"}]
        )
        assert "symptoms" in result or "error" in result
        print(f"Service result: {result}")

    def test_service_unknown_intent(self, query_service):
        """Test query service with unknown intent."""
        result = query_service.execute_intent(Intent.UNKNOWN, [])
        assert "error" in result

    def test_natural_query_flu(self, query_service):
        """Test natural query processing for flu."""
        result = query_service.natural_query("How is flu treated?")
        assert result is not None
        print(f"Flu treatment query: {result}")


class TestResponseGeneration:
    """Test response generation."""

    def test_generate_symptoms_response(self, response_gen):
        """Test response generation for symptoms."""
        result = {
            "disease": "Hypertension",
            "symptoms": [
                {"name": "Headache"},
                {"name": "Dizziness"}
            ],
            "count": 2
        }
        response = response_gen.generate_response("get_symptoms", result)
        assert "response" in response
        assert "Headache" in response["response"]
        assert response["confidence"] > 0

    def test_generate_explanation(self, response_gen):
        """Test explanation generation."""
        result = {"disease": "Hypertension", "count": 4}
        explanation = response_gen.generate_explanation("get_symptoms", result)
        assert len(explanation) > 0
        assert "Hypertension" in explanation

    def test_confidence_calculation(self, response_gen):
        """Test confidence calculation."""
        result = {"disease": "Hypertension", "count": 5}
        confidence, metrics = response_gen.calculate_confidence(result, "get_symptoms")
        assert 0 <= confidence <= 1
        assert metrics.has_data is True

    def test_empty_result_confidence(self, response_gen):
        """Test confidence with empty results."""
        result = {}
        confidence, metrics = response_gen.calculate_confidence(result, "get_symptoms")
        assert confidence == 0.0
        assert metrics.has_data is False

    def test_suggestions_generation(self, response_gen):
        """Test suggestions generation."""
        result = {"disease": "Hypertension", "count": 4}
        suggestions = response_gen.generate_suggestions("get_symptoms", result)
        assert len(suggestions) <= 3
        print(f"Suggestions: {suggestions}")


class TestContextManagement:
    """Test conversation context handling."""

    def test_context_update(self, context_mgr):
        """Test context updates correctly."""
        context = context_mgr.get_context("test_session")
        context.update(
            intent="get_symptoms",
            disease="Hypertension",
            symptoms=["Headache", "Dizziness"]
        )
        assert context.last_disease == "Hypertension"
        assert len(context.last_symptoms) == 2
        assert context.conversation_turns == 1

    def test_follow_up_detection(self, context_mgr):
        """Test follow-up question detection."""
        context = context_mgr.get_context("test_session2")
        context.update(intent="get_symptoms", disease="Hypertension")
        context.conversation_turns = 1

        # Short follow-up should use context
        can_use = context.can_use_context("How is it treated?")
        assert can_use is True

    def test_context_clear(self, context_mgr):
        """Test context clearing."""
        context = context_mgr.get_context("test_session3")
        context.update(intent="get_symptoms", disease="Hypertension")
        context.clear()
        assert context.last_disease is None
        assert context.conversation_turns == 0


class TestChatbotPipeline:
    """Integration test for full chatbot pipeline."""

    def test_pipeline_symptoms(self, db, nlp, query_service, response_gen):
        """Test full pipeline for symptoms query."""
        query = "What are symptoms of hypertension?"
        parsed = nlp.parse(query)
        result = query_service.execute_intent(parsed.intent, parsed.entities)
        response = response_gen.generate_response(parsed.intent.value, result)

        assert response["response"] is not None
        assert len(response["explanation"]) > 0
        print(f"Full pipeline response: {response}")

    def test_pipeline_follow_up(self, db, nlp, query_service, response_gen, context_mgr):
        """Test pipeline with follow-up question."""
        session_id = "test_followup"

        # First query
        q1 = "What are symptoms of hypertension?"
        p1 = nlp.parse(q1)
        r1 = query_service.execute_intent(p1.intent, p1.entities)
        context_mgr.update_context(session_id, p1.intent.value, disease="Hypertension")

        # Follow-up query
        q2 = "How is it treated?"
        enriched = context_mgr.enrich_query(q2, session_id)
        p2 = nlp.parse(enriched)
        r2 = query_service.execute_intent(p2.intent, p2.entities)
        response = response_gen.generate_response(p2.intent.value, r2)

        assert response["response"] is not None
        print(f"Follow-up response: {response}")


class TestCypherQueries:
    """PART 3: Data Integrity - Cypher Validation Queries"""

    @staticmethod
    def get_duplicate_nodes_query():
        """Find duplicate nodes (same type and name)."""
        return """
        MATCH (n)
        WITH n.__entityType__ AS type, n.name AS name, collect(n.id) AS ids, count(*) AS cnt
        WHERE cnt > 1
        RETURN type, name, ids, cnt
        """

    @staticmethod
    def get_orphan_nodes_query():
        """Find orphan nodes (no relationships)."""
        return """
        MATCH (n)
        WHERE NOT exists(()-[]->(n)) AND NOT exists((n)-[]->())
        RETURN n.__entityType__ AS type, n.id AS id, n.name AS name
        """

    @staticmethod
    def get_unconnected_diseases_query():
        """Find diseases without symptoms or treatments."""
        return """
        MATCH (d:Disease)
        WHERE NOT exists((d)-[:HAS_SYMPTOM]->()) OR NOT exists((d)-[:TREATED_BY]->())
        RETURN d.id AS id, d.name AS name,
               exists((d)-[:HAS_SYMPTOM]->()) AS has_symptoms,
               exists((d)-[:TREATED_BY]->()) AS has_treatments
        """

    @staticmethod
    def get_isolated_symptoms_query():
        """Find symptoms not connected to any disease."""
        return """
        MATCH (s:Symptom)
        WHERE NOT exists(()-[:HAS_SYMPTOM]->(s))
        RETURN count(s) AS isolated_symptom_count
        """

    @staticmethod
    def get_relationship_integrity_query():
        """Check relationship integrity (source/target validity)."""
        return """
        MATCH ()-[r]->()
        WHERE startNode(r) IS NULL OR endNode(r) IS NULL
        RETURN count(r) AS invalid_relationships
        """


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
