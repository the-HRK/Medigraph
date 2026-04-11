"""
Response Generator
Creates natural language responses from query results with explainability
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ResponseMetrics:
    """Metrics about the generated response."""
    confidence: float  # 0.0 to 1.0
    result_count: int
    has_data: bool
    is_exact_match: bool
    sources: List[str]


class ResponseGenerator:
    """
    Generates natural language responses from structured query results.
    Includes explainability and confidence scoring.
    """

    def __init__(self):
        self.max_display_items = 7

    def calculate_confidence(self, result: Dict[str, Any], intent: str) -> Tuple[float, ResponseMetrics]:
        """Calculate confidence score based on result quality."""
        has_data = bool(result and not result.get("error"))

        if not has_data:
            return 0.0, ResponseMetrics(
                confidence=0.0,
                result_count=0,
                has_data=False,
                is_exact_match=False,
                sources=["no_data"]
            )

        # Base confidence on result count and data completeness
        count = result.get("count", 0)
        is_exact_match = count > 0

        # Calculate confidence
        confidence = 0.5  # Base confidence

        if is_exact_match:
            confidence += 0.3

        if count > 0:
            # More results = higher confidence (for selection quality)
            confidence += min(0.2, count * 0.02)

        # Exact disease match increases confidence
        if result.get("disease"):
            confidence += 0.1

        confidence = min(1.0, confidence)

        metrics = ResponseMetrics(
            confidence=confidence,
            result_count=count,
            has_data=has_data,
            is_exact_match=is_exact_match,
            sources=["neo4j_graph_database"]
        )

        return confidence, metrics

    def format_symptoms(self, symptoms: List[Dict]) -> str:
        """Format symptoms list into readable text."""
        if not symptoms:
            return "No symptoms found"

        names = [s.get("name", str(s)) for s in symptoms[:self.max_display_items]]
        if len(symptoms) > self.max_display_items:
            names.append(f"and {len(symptoms) - self.max_display_items} more")

        return self._humanize_list(names)

    def format_treatments(self, treatments: List[Dict]) -> str:
        """Format treatments list into readable text."""
        if not treatments:
            return "No treatments found"

        formatted = []
        for t in treatments[:self.max_display_items]:
            name = t.get("name", "Unknown")
            efficacy = t.get("efficacy", "")
            if efficacy:
                formatted.append(f"{name} ({efficacy} efficacy)")
            else:
                formatted.append(name)

        if len(treatments) > self.max_display_items:
            formatted.append(f"and {len(treatments) - self.max_display_items} more")

        return self._humanize_list(formatted, use_and=True)

    def format_diseases(self, diseases: List[Dict]) -> str:
        """Format diseases list into readable text."""
        if not diseases:
            return "No diseases found"

        names = []
        for d in diseases[:self.max_display_items]:
            name = d.get("name", "Unknown")
            severity = d.get("severity", "")
            if severity:
                names.append(f"{name} ({severity})")
            else:
                names.append(name)

        if len(diseases) > self.max_display_items:
            names.append(f"and {len(diseases) - self.max_display_items} more")

        return self._humanize_list(names, use_and=True)

    def format_interactions(self, interactions: List[Dict]) -> str:
        """Format drug interactions into readable text."""
        if not interactions:
            return "No known interactions"

        formatted = []
        for i in interactions[:self.max_display_items]:
            name = i.get("name", "Unknown")
            severity = i.get("severity", "unknown")
            interaction_type = i.get("interaction_type", "")
            formatted.append(f"{name} ({severity} {interaction_type})")

        if len(interactions) > self.max_display_items:
            formatted.append(f"and {len(interactions) - self.max_display_items} more")

        return self._humanize_list(formatted, use_and=True)

    def _humanize_list(self, items: List[str], use_and: bool = False) -> str:
        """Convert list to human-readable string."""
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}" if use_and else f"{items[0]}, {items[1]}"

        return ", ".join(items[:-1]) + f", and {items[-1]}"

    def generate_explanation(self, intent: str, result: Dict[str, Any],
                           context: Optional[Any] = None) -> str:
        """Generate explainability text - WHY this answer is given."""
        explanations = {
            "get_symptoms": self._explain_symptoms,
            "get_treatments": self._explain_treatments,
            "find_diseases": self._explain_find_diseases,
            "drug_interactions": self._explain_interactions,
            "predict_disease": self._explain_prediction,
            "get_info": self._explain_info,
            "find_related": self._explain_related,
        }

        explain_func = explanations.get(intent, self._explain_generic)
        return explain_func(result, context)

    def _explain_symptoms(self, result: Dict, context: Optional[Any]) -> str:
        """Explain why symptoms were returned."""
        disease = result.get("disease", "the disease")
        count = result.get("count", 0)
        return f"These symptoms are directly connected to {disease} in the medical knowledge graph. Found {count} associated symptoms."

    def _explain_treatments(self, result: Dict, context: Optional[Any]) -> str:
        """Explain why treatments were returned."""
        disease = result.get("disease", "the disease")
        count = result.get("count", 0)
        return f"These treatments are documented treatments for {disease}. The graph contains {count} treatment options."

    def _explain_find_diseases(self, result: Dict, context: Optional[Any]) -> str:
        """Explain how diseases were found."""
        symptom = result.get("symptom", "the symptom")
        count = result.get("count", 0)
        return f"Diseases were found by matching the symptom '{symptom}' in the knowledge graph. {count} diseases share this symptom."

    def _explain_interactions(self, result: Dict, context: Optional[Any]) -> str:
        """Explain drug interaction findings."""
        if "drug2" in result:
            drug1, drug2 = result.get("drug1", ""), result.get("drug2", "")
            if result.get("has_interaction"):
                return f"Interaction data found between {drug1} and {drug2} in drug relationship graph."
            return f"No documented interaction found between {drug1} and {drug2} in the database."
        drug = result.get("drug", "the drug")
        count = result.get("count", 0)
        return f"Drug interactions for {drug} found by checking the interaction network. {count} known interactions."

    def _explain_prediction(self, result: Dict, context: Optional[Any]) -> str:
        """Explain disease prediction."""
        symptoms = result.get("input_symptoms", [])
        count = result.get("count", 0)
        return f"Disease prediction based on matching your symptoms ({', '.join(symptoms)}) against the knowledge graph. {count} conditions match."

    def _explain_info(self, result: Dict, context: Optional[Any]) -> str:
        """Explain disease info retrieval."""
        disease = result.get("disease", {}).get("name", "Unknown")
        return f"Information retrieved from the medical knowledge graph for {disease}."

    def _explain_related(self, result: Dict, context: Optional[Any]) -> str:
        """Explain related diseases finding."""
        disease = result.get("disease", "the disease")
        count = result.get("count", 0)
        return f"Related diseases found by analyzing shared symptoms and category with {disease}. {count} related conditions."

    def _explain_generic(self, result: Dict, context: Optional[Any]) -> str:
        """Generic explanation."""
        return "This information is retrieved from the Medigraph medical knowledge graph."

    def generate_suggestions(self, intent: str, result: Dict[str, Any],
                            context: Optional[Any] = None) -> List[str]:
        """Generate helpful follow-up suggestions."""
        suggestions = []

        # Handle both dict context and ConversationContext object
        if context is None:
            disease = result.get("disease")
        elif hasattr(context, 'last_disease'):
            disease = result.get("disease") or context.last_disease
        else:
            disease = result.get("disease", context.get("last_disease") if context else None)

        if intent == "get_symptoms" and disease:
            suggestions.append(f"Ask about treatments for {disease}")
            suggestions.append("Find related diseases")

        elif intent == "get_treatments" and disease:
            suggestions.append(f"Learn more about {disease}")
            suggestions.append("Check drug interactions")

        elif intent == "find_diseases":
            symptom = result.get("symptom")
            if symptom:
                suggestions.append(f"Get treatment options for these diseases")
                suggestions.append("Learn about prevention")

        elif intent == "drug_interactions":
            suggestions.append("Check side effects")
            suggestions.append("Find alternatives")

        elif intent == "predict_disease":
            suggestions.append("Get detailed information about each condition")
            suggestions.append("Learn about treatment options")

        elif intent == "get_info":
            suggestions.append("View the knowledge graph")
            suggestions.append("Find related conditions")

        return suggestions[:3]  # Max 3 suggestions

    def generate_response(self, intent: str, result: Dict[str, Any],
                        context: Optional[Any] = None) -> Dict[str, Any]:
        """
        Generate complete response with explanation and suggestions.
        """
        # Handle errors
        if "error" in result and "hint" in result:
            return {
                "response": f"I couldn't understand that. {result.get('hint', '')}",
                "confidence": 0.0,
                "confidence_label": "No confidence",
                "explanation": "The query could not be processed.",
                "suggestions": [
                    "Try: 'What are symptoms of diabetes?'",
                    "Try: 'How is hypertension treated?'",
                    "Try: 'What diseases cause chest pain?'"
                ],
                "intent": intent,
                "data": result
            }

        if "error" in result:
            return {
                "response": f"I found an issue: {result.get('error', 'Unknown error')}",
                "confidence": 0.0,
                "confidence_label": "No confidence",
                "explanation": "An error occurred while querying the database.",
                "suggestions": [],
                "intent": intent,
                "data": result
            }

        # Calculate confidence
        confidence, metrics = self.calculate_confidence(result, intent)

        # Generate main response
        response = self._build_main_response(intent, result)

        # Generate explanation
        explanation = self.generate_explanation(intent, result, context)

        # Generate suggestions
        suggestions = self.generate_suggestions(intent, result, context)

        return {
            "response": response,
            "confidence": confidence,
            "confidence_label": self._get_confidence_label(confidence),
            "explanation": explanation,
            "suggestions": suggestions,
            "intent": intent,
            "data": result,
            "metadata": {
                "result_count": metrics.result_count,
                "sources": metrics.sources,
                "is_exact_match": metrics.is_exact_match
            }
        }

    def _build_main_response(self, intent: str, result: Dict[str, Any]) -> str:
        """Build the main response text."""
        handlers = {
            "get_symptoms": self._handle_symptoms,
            "get_treatments": self._handle_treatments,
            "find_diseases": self._handle_find_diseases,
            "drug_interactions": self._handle_interactions,
            "predict_disease": self._handle_prediction,
            "get_info": self._handle_info,
            "find_related": self._handle_related,
            "search": self._handle_search,
        }

        handler = handlers.get(intent, self._handle_generic)
        return handler(result)

    def _handle_symptoms(self, result: Dict) -> str:
        disease = result.get("disease", "the disease")
        symptoms = result.get("symptoms", [])

        if not symptoms:
            return f"I don't have symptom data for {disease} in the database."

        formatted = self.format_symptoms(symptoms)
        count = result.get("count", 0)

        return f"The symptoms of {disease} include: {formatted}. (Found {count} symptoms in the knowledge graph)"

    def _handle_treatments(self, result: Dict) -> str:
        disease = result.get("disease", "the disease")
        treatments = result.get("treatments", [])

        if not treatments:
            return f"I don't have treatment data for {disease} in the database."

        formatted = self.format_treatments(treatments)
        count = result.get("count", 0)

        return f"{disease} can be treated with: {formatted}. ({count} treatment options available)"

    def _handle_find_diseases(self, result: Dict) -> str:
        symptom = result.get("symptom", "that symptom")
        diseases = result.get("diseases", [])
        count = result.get("count", 0)

        if not diseases:
            return f"No diseases are associated with the symptom '{symptom}' in the database."

        formatted = self.format_diseases(diseases)
        return f"Diseases associated with '{symptom}': {formatted}. (Found {count} matching conditions)"

    def _handle_interactions(self, result: Dict) -> str:
        if "drug2" in result:
            drug1, drug2 = result.get("drug1", ""), result.get("drug2", "")
            has_interaction = result.get("has_interaction", False)

            if has_interaction:
                interactions = result.get("interactions", [])
                if interactions:
                    interaction = interactions[0]
                    interaction_type = interaction.get("interaction_type", "interaction")
                    severity = interaction.get("severity", "unknown")
                    return f"Yes, {drug1} and {drug2} may interact. This is a {severity} {interaction_type}. Consult your healthcare provider."

            return f"No known interactions between {drug1} and {drug2} were found in the database."

        drug = result.get("drug", "the drug")
        interactions = result.get("interactions", [])
        count = result.get("count", 0)

        if not interactions:
            return f"No drug interactions for {drug} were found in the database."

        formatted = self.format_interactions(interactions)
        return f"{drug} may interact with: {formatted}. ({count} known interactions)"

    def _handle_prediction(self, result: Dict) -> str:
        symptoms = result.get("input_symptoms", [])
        diseases = result.get("predicted_diseases", [])
        count = result.get("count", 0)

        if not diseases:
            return f"Based on symptoms ({', '.join(symptoms)}), I couldn't find matching conditions in the database."

        formatted = self.format_diseases(diseases)
        return f"Based on your symptoms ({', '.join(symptoms)}), possible conditions include: {formatted}. (Found {count} matching conditions)"

    def _handle_info(self, result: Dict) -> str:
        disease_data = result.get("disease", {})
        disease = disease_data.get("name", "Unknown")
        category = disease_data.get("category", "Unknown")
        severity = disease_data.get("severity", "Unknown")
        description = disease_data.get("description", "")
        symptoms = [s for s in disease_data.get("symptoms", []) if s]
        treatments = [t for t in disease_data.get("treatments", []) if t]

        parts = [f"{disease} is a {severity.lower()} {category.lower()} condition."]

        if description:
            parts.append(f" {description}")

        if symptoms:
            parts.append(f" Common symptoms include: {self.format_symptoms([{'name': s} for s in symptoms[:5]])}.")

        if treatments:
            parts.append(f" Treatment options are available.")

        return "".join(parts)

    def _handle_related(self, result: Dict) -> str:
        disease = result.get("disease", "that disease")
        related = result.get("related_diseases", [])
        count = result.get("count", 0)

        if not related:
            return f"No related diseases to {disease} were found in the database."

        formatted = self.format_diseases(related)
        return f"Diseases related to {disease}: {formatted}. ({count} related conditions)"

    def _handle_search(self, result: Dict) -> str:
        query = result.get("query", "")
        results = result.get("results", [])
        count = result.get("count", 0)

        if not results:
            return f"No results found for '{query}' in the database."

        items = []
        for r in results[:5]:
            entity_type = r.get("entity_type", "unknown")
            name = r.get("name", "Unknown")
            items.append(f"{name} ({entity_type})")

        formatted = self._humanize_list(items)
        return f"Found {count} results for '{query}': {formatted}"

    def _handle_generic(self, result: Dict) -> str:
        return "I found some information about your query."

    def _get_confidence_label(self, confidence: float) -> str:
        """Convert confidence score to label."""
        if confidence >= 0.9:
            return "High confidence"
        elif confidence >= 0.7:
            return "Good confidence"
        elif confidence >= 0.5:
            return "Moderate confidence"
        elif confidence > 0:
            return "Low confidence"
        return "No confidence"


# Global instance
_response_generator: Optional[ResponseGenerator] = None


def get_response_generator() -> ResponseGenerator:
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
