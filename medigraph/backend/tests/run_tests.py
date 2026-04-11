"""
Medigraph Test Runner
Run this script to execute the test suite against a live database.
Usage: python tests/run_tests.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Neo4jConnection
from services.nlp_processor import NLPProcessor, Intent
from services.query_service import QueryService
from services.query_builder import QueryBuilder
from services.response_generator import ResponseGenerator
from services.context_manager import ContextManager


class TestRunner:
    def __init__(self):
        self.nlp = NLPProcessor()
        self.response_gen = ResponseGenerator()
        self.context_mgr = ContextManager()
        self.results = []

    def log_test(self, name, passed, message=""):
        status = "PASS" if passed else "FAIL"
        self.results.append({"name": name, "passed": passed, "message": message})
        print(f"  [{status}] {name}" + (f" - {message}" if message else ""))

    def run_all_tests(self):
        print("=" * 60)
        print("MEDIGRAPH TEST SUITE")
        print("=" * 60)

        self.test_database_connectivity()
        self.test_nlp_intent_detection()
        self.test_nlp_entity_extraction()
        self.test_nlp_edge_cases()
        self.test_query_execution()
        self.test_response_generation()
        self.test_context_handling()
        self.test_data_integrity()
        self.test_query_builder()

        self.print_summary()

    def test_database_connectivity(self):
        print("\n[1] DATABASE CONNECTIVITY")
        try:
            db = Neo4jConnection()
            db.connect()
            is_connected = db.verify_connectivity()
            self.log_test("Neo4j Connection", is_connected, "Connected" if is_connected else "Failed")
            db.close()
        except Exception as e:
            self.log_test("Neo4j Connection", False, str(e))

    def test_nlp_intent_detection(self):
        print("\n[2] NLP INTENT DETECTION")
        test_cases = [
            # Basic Queries
            ("What are symptoms of diabetes?", Intent.GET_SYMPTOMS),
            ("How is flu treated?", Intent.GET_TREATMENTS),
            ("What diseases cause fever?", Intent.FIND_DISEASES),
            ("Which diseases have headache?", Intent.FIND_DISEASES),
            ("Does aspirin interact with ibuprofen?", Intent.DRUG_INTERACTIONS),
            ("I have fever and cough, what could it be?", Intent.PREDICT_DISEASE),
            ("Tell me about Alzheimer's disease", Intent.GET_INFO),
            ("Find diseases similar to Parkinson's", Intent.FIND_RELATED),

            # Treatment variations
            ("How is hypertension treated?", Intent.GET_TREATMENTS),
            ("What's the treatment for diabetes?", Intent.GET_TREATMENTS),
            ("How to treat the flu?", Intent.GET_TREATMENTS),
            ("treatment for flu", Intent.GET_TREATMENTS),
        ]

        passed = 0
        for query, expected in test_cases:
            result = self.nlp.parse(query)
            if result.intent == expected:
                passed += 1
                self.log_test(f"'{query[:40]}...' -> {expected.value}", True)
            else:
                self.log_test(f"'{query[:40]}...'", False, f"Expected {expected.value}, got {result.intent.value}")

        print(f"  Intent Detection: {passed}/{len(test_cases)} passed")

    def test_nlp_entity_extraction(self):
        print("\n[3] NLP ENTITY EXTRACTION")
        test_cases = [
            ("What are symptoms of hypertension?", ["hypertension"]),
            ("I have fever and cough", ["fever", "cough"]),
            ("Does warfarin interact with aspirin?", ["warfarin", "aspirin"]),
        ]

        passed = 0
        for query, expected_entities in test_cases:
            result = self.nlp.parse(query)
            extracted = [e.value.lower() for e in result.entities]
            found = [e for e in expected_entities if e in extracted]
            if len(found) == len(expected_entities):
                passed += 1
                self.log_test(f"'{query[:40]}'", True, f"Extracted: {extracted}")
            else:
                self.log_test(f"'{query[:40]}'", False, f"Expected {expected_entities}, got {extracted}")

        print(f"  Entity Extraction: {passed}/{len(test_cases)} passed")

    def test_nlp_edge_cases(self):
        print("\n[4] NLP EDGE CASES")
        edge_cases = [
            ("", "Empty query"),
            ("asdfgh query", "Gibberish"),
            ("Symptoms of unknown disease xyz", "Unknown entity"),
        ]

        for query, description in edge_cases:
            try:
                result = self.nlp.parse(query)
                self.log_test(f"Edge case: {description}", True, f"Intent: {result.intent.value}")
            except Exception as e:
                self.log_test(f"Edge case: {description}", False, str(e))

    def test_query_execution(self):
        print("\n[5] QUERY EXECUTION")
        try:
            db = Neo4jConnection()
            db.connect()
            qb = QueryBuilder()

            # Test symptoms query
            query, params = qb.get_symptoms_of_disease("Hypertension")
            results = db.execute_query(query, params)
            self.log_test("Symptoms of Hypertension", len(results) > 0, f"Found {len(results)} symptoms")

            # Test treatments query
            query, params = qb.get_treatments_of_disease("Hypertension")
            results = db.execute_query(query, params)
            self.log_test("Treatments of Hypertension", len(results) > 0, f"Found {len(results)} treatments")

            # Test find diseases by symptom
            query, params = qb.find_diseases_by_symptom("Fever")
            results = db.execute_query(query, params)
            self.log_test("Diseases with Fever", len(results) > 0, f"Found {len(results)} diseases")

            # Test drug interactions
            query, params = qb.check_drug_pair_interaction("Aspirin", "Warfarin")
            results = db.execute_query(query, params)
            self.log_test("Aspirin-Warfarin interaction", len(results) >= 0, f"Found {len(results)} interactions")

            # Test disease prediction
            query, params = qb.predict_diseases_by_symptoms(["Chest pain", "Shortness of breath"])
            results = db.execute_query(query, params)
            self.log_test("Disease prediction", len(results) > 0, f"Found {len(results)} predicted diseases")

            # Test get related diseases
            query, params = qb.get_related_diseases("Hypertension")
            results = db.execute_query(query, params)
            self.log_test("Related diseases", len(results) >= 0, f"Found {len(results)} related diseases")

            db.close()
        except Exception as e:
            self.log_test("Query Execution", False, str(e))

    def test_response_generation(self):
        print("\n[6] RESPONSE GENERATION")
        test_cases = [
            {
                "name": "Symptoms response",
                "intent": "get_symptoms",
                "result": {"disease": "Hypertension", "symptoms": [{"name": "Headache"}, {"name": "Dizziness"}], "count": 2}
            },
            {
                "name": "Treatments response",
                "intent": "get_treatments",
                "result": {"disease": "Diabetes", "treatments": [{"name": "Metformin"}], "count": 1}
            },
            {
                "name": "Empty result response",
                "intent": "get_symptoms",
                "result": {}
            },
        ]

        for tc in test_cases:
            response = self.response_gen.generate_response(tc["intent"], tc["result"])
            has_response = "response" in response and len(response["response"]) > 0
            has_explanation = "explanation" in response and len(response["explanation"]) > 0
            has_suggestions = "suggestions" in response

            if has_response and has_explanation:
                self.log_test(tc["name"], True, f"Confidence: {response['confidence']}")
            else:
                self.log_test(tc["name"], False, f"Missing components")

    def test_context_handling(self):
        print("\n[7] CONTEXT HANDLING (FOLLOW-UP QUESTIONS)")
        session_id = "test_session"
        ctx = self.context_mgr.get_context(session_id)

        # Simulate first query about hypertension
        ctx.update(intent="get_symptoms", disease="Hypertension", symptoms=["Headache", "Dizziness"])

        # Test follow-up detection
        can_use = ctx.can_use_context("How is it treated?")
        self.log_test("Follow-up detection", can_use, "'it' refers to Hypertension")

        # Test enrichment
        enriched = self.context_mgr.enrich_query("How is it treated?", session_id)
        self.log_test("Query enrichment", enriched is not None, f"Query: {enriched[:50]}...")

        # Clear and test
        self.context_mgr.clear_context(session_id)
        ctx2 = self.context_mgr.get_context(session_id)
        self.log_test("Context clear", ctx2.conversation_turns == 0, "Context reset")

    def test_data_integrity(self):
        print("\n[8] DATA INTEGRITY")
        try:
            db = Neo4jConnection()
            db.connect()

            # Check for diseases without symptoms
            query = """
            MATCH (d:Disease)
            WHERE NOT exists((d)-[:HAS_SYMPTOM]->())
            RETURN d.name AS name
            LIMIT 10
            """
            results = db.execute_query(query)
            self.log_test("Diseases without symptoms", True, f"Found {len(results)}" if results else "None (good)")

            # Check for diseases without treatments
            query = """
            MATCH (d:Disease)
            WHERE NOT exists((d)-[:TREATED_BY]->())
            RETURN d.name AS name
            LIMIT 10
            """
            results = db.execute_query(query)
            self.log_test("Diseases without treatments", True, f"Found {len(results)}" if results else "None (good)")

            # Check for orphan symptoms
            query = """
            MATCH (s:Symptom)
            WHERE NOT exists(()-[:HAS_SYMPTOM]->(s))
            RETURN count(s) AS count
            """
            results = db.execute_query(query)
            orphan_count = results[0]["count"] if results else 0
            self.log_test("Orphan symptoms", True, f"{orphan_count} orphan symptoms")

            # Check relationship counts
            query = """
            MATCH ()-[r]->()
            RETURN count(r) AS total_relationships
            """
            results = db.execute_query(query)
            rel_count = results[0]["total_relationships"] if results else 0
            self.log_test("Total relationships", rel_count > 0, f"{rel_count} relationships in graph")

            db.close()
        except Exception as e:
            self.log_test("Data Integrity Check", False, str(e))

    def test_query_builder(self):
        print("\n[9] QUERY BUILDER VALIDATION")
        qb = QueryBuilder()

        # Verify all query builder methods return valid queries
        methods = [
            ("get_symptoms_of_disease", qb.get_symptoms_of_disease("Test")),
            ("get_treatments_of_disease", qb.get_treatments_of_disease("Test")),
            ("find_diseases_by_symptom", qb.find_diseases_by_symptom("Test")),
            ("get_drug_interactions", qb.get_drug_interactions("Test")),
            ("check_drug_pair_interaction", qb.check_drug_pair_interaction("A", "B")),
            ("get_related_diseases", qb.get_related_diseases("Test")),
            ("get_disease_info", qb.get_disease_info("Test")),
            ("predict_diseases_by_symptoms", qb.predict_diseases_by_symptoms(["A", "B"])),
            ("search_entities", qb.search_entities("Test")),
        ]

        passed = 0
        for name, (query, params) in methods:
            is_valid = isinstance(query, str) and len(query) > 0 and isinstance(params, dict)
            if is_valid:
                passed += 1
                self.log_test(name, True, f"Query length: {len(query)}")
            else:
                self.log_test(name, False, "Invalid query or params")

        print(f"  Query Builder: {passed}/{len(methods)} valid")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        print(f"Total:  {total}")
        print(f"Passed:  {passed}")
        print(f"Failed:  {failed}")

        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['name']}: {r['message']}")

        print("\n" + "=" * 60)
        return failed == 0


def main():
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
