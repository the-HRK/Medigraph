"""
Query Execution Service
Executes Cypher queries and formats results
"""
from typing import Any, Dict, List, Optional
from database.connection import Neo4jConnection
from services.query_builder import QueryBuilder
from services.nlp_processor import Intent, NLPProcessor, get_nlp_processor


class QueryService:
    def __init__(self, db: Neo4jConnection):
        self.db = db
        self.query_builder = QueryBuilder()
        self.nlp = get_nlp_processor()

    def execute_intent(self, intent: Intent, entities: List[Any]) -> Dict[str, Any]:
        """Route intent to appropriate query builder method."""

        if not entities:
            return {"error": "No entities found in query", "intent": intent.value}

        entity_values = {e.type: e.value for e in entities}

        try:
            if intent == Intent.GET_SYMPTOMS:
                disease = entity_values.get("disease", "")
                query, params = self.query_builder.get_symptoms_of_disease(disease)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "disease": disease,
                    "symptoms": results,
                    "count": len(results)
                }

            elif intent == Intent.GET_TREATMENTS:
                disease = entity_values.get("disease", "")
                query, params = self.query_builder.get_treatments_of_disease(disease)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "disease": disease,
                    "treatments": results,
                    "count": len(results)
                }

            elif intent == Intent.FIND_DISEASES:
                symptom = entity_values.get("symptom", "")
                query, params = self.query_builder.find_diseases_by_symptom(symptom)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "symptom": symptom,
                    "diseases": results,
                    "count": len(results)
                }

            elif intent == Intent.DRUG_INTERACTIONS:
                drug1 = entity_values.get("drug", "")
                # If two drugs found, check specific interaction
                drug_entities = [e for e in entities if e.type == "drug"]
                if len(drug_entities) >= 2:
                    drug1 = drug_entities[0].value
                    drug2 = drug_entities[1].value
                    query, params = self.query_builder.check_drug_pair_interaction(drug1, drug2)
                    results = self.db.execute_query(query, params)
                    return {
                        "intent": intent.value,
                        "drug1": drug1,
                        "drug2": drug2,
                        "interactions": results,
                        "has_interaction": len(results) > 0
                    }
                else:
                    query, params = self.query_builder.get_drug_interactions(drug1)
                    results = self.db.execute_query(query, params)
                    return {
                        "intent": intent.value,
                        "drug": drug1,
                        "interactions": results,
                        "count": len(results)
                    }

            elif intent == Intent.PREDICT_DISEASE:
                symptoms = [e.value for e in entities if e.type == "symptom"]
                query, params = self.query_builder.predict_diseases_by_symptoms(symptoms)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "input_symptoms": symptoms,
                    "predicted_diseases": results,
                    "count": len(results)
                }

            elif intent == Intent.GET_INFO:
                disease = entity_values.get("disease", "")
                query, params = self.query_builder.get_disease_info(disease)
                results = self.db.execute_query(query, params)
                if results:
                    return {
                        "intent": intent.value,
                        "disease": results[0]
                    }
                return {"error": f"Disease '{disease}' not found", "intent": intent.value}

            elif intent == Intent.FIND_RELATED:
                disease = entity_values.get("disease", "")
                query, params = self.query_builder.get_related_diseases(disease)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "disease": disease,
                    "related_diseases": results,
                    "count": len(results)
                }

            elif intent == Intent.SEARCH:
                search_term = list(entity_values.values())[0] if entity_values else ""
                if not search_term:
                    return {"error": "No search term provided", "intent": intent.value}
                query, params = self.query_builder.search_entities(search_term)
                results = self.db.execute_query(query, params)
                return {
                    "intent": intent.value,
                    "query": search_term,
                    "results": results,
                    "count": len(results)
                }

            else:
                return {
                    "error": f"Intent '{intent.value}' not supported",
                    "intent": intent.value
                }

        except Exception as e:
            return {
                "error": str(e),
                "intent": intent.value,
                "entities": [e.dict() for e in entities]
            }

    def natural_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query end-to-end."""
        parsed = self.nlp.parse(query)

        if parsed.intent == Intent.UNKNOWN:
            # Try to search anyway
            entities = parsed.entities
            if entities:
                return self.execute_intent(Intent.SEARCH, entities)
            return {
                "error": "Could not understand query",
                "original_query": query,
                "hint": "Try asking: 'What are symptoms of diabetes?' or 'Find drugs for hypertension'"
            }

        return self.execute_intent(parsed.intent, parsed.entities)


def get_query_service(db: Neo4jConnection) -> QueryService:
    return QueryService(db)
