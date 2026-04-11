"""
NLP Processing Service
Rule-based intent detection and entity extraction for medical queries
"""
import re
from enum import Enum
from typing import List, Tuple, Optional
from pydantic import BaseModel


class Intent(str, Enum):
    GET_SYMPTOMS = "get_symptoms"
    GET_TREATMENTS = "get_treatments"
    FIND_DISEASES = "find_diseases"
    DRUG_INTERACTIONS = "drug_interactions"
    PREDICT_DISEASE = "predict_disease"
    GET_INFO = "get_info"
    FIND_RELATED = "find_related"
    SEARCH = "search"
    UNKNOWN = "unknown"


class Entity(BaseModel):
    type: str  # disease, symptom, drug, category
    value: str
    original: str


class ParsedQuery(BaseModel):
    intent: Intent
    entities: List[Entity]
    raw_query: str


class NLPProcessor:
    """
    Rule-based NLP processor for medical queries.
    Uses pattern matching and keyword detection.
    """

    # Symptom keywords
    SYMPTOM_WORDS = [
        "symptom", "symptoms", "sign", "signs", "manifestation", "manifestations",
        "presenting", "complain", "experiencing", "feel", "feeling"
    ]

    # Treatment keywords
    TREATMENT_WORDS = [
        "treatment", "treatments", "therapy", "medication", "medications",
        "drug", "drugs", "medicine", "medicines", "cure", "manage"
    ]

    # Disease prediction keywords
    PREDICT_WORDS = [
        "predict", "diagnose", "diagnosis", "likely", "possible", "could be",
        "might be", "what disease", "what condition", "caused by"
    ]

    # Interaction keywords
    INTERACTION_WORDS = [
        "interact", "interaction", "interactions", "combine", "with", "together",
        "alongside", "concurrently"
    ]

    # Info keywords
    INFO_WORDS = [
        "info", "information", "about", "details", "what is", "tell me"
    ]

    # Related keywords
    RELATED_WORDS = [
        "related", "similar", "like", "also", "associated", "connected"
    ]

    # Known diseases (subset for matching)
    KNOWN_DISEASES = [
        "hypertension", "diabetes", "asthma", "copd", "cancer", "stroke",
        "epilepsy", "migraine", "arthritis", "pneumonia", "bronchitis",
        "gastritis", "hepatitis", "anemia", "thyroid", "depression",
        "anxiety", "schizophrenia", "bipolar", "dementia", "alzheimer",
        "parkinson", "multiple sclerosis", "lupus", "fibromyalgia",
        "flu", "influenza", "cold", "fever", "malaria", "tb", "tuberculosis",
        "hiv", "aids", "measles", "chickenpox", "covid", "covid-19"
    ]

    # Known symptoms
    KNOWN_SYMPTOMS = [
        "chest pain", "shortness of breath", "fatigue", "dizziness", "headache",
        "fever", "cough", "nausea", "vomiting", "diarrhea", "constipation",
        "abdominal pain", "joint pain", "muscle weakness", "rash", "itching",
        "weight loss", "weight gain", "thirst", "frequent urination", "night sweats",
        "seizures", "tremor", "numbness", "blurred vision", "edema", "syncope",
        "hematuria", "jaundice", "confusion", "anxiety", "low mood", "insomnia",
        "back pain", "stiffness", "swelling", "loss of appetite", "heartburn",
        "palpitations", "wheezing"
    ]

    # Known drugs
    KNOWN_DRUGS = [
        "lisinopril", "metformin", "atorvastatin", "amlodipine", "metoprolol",
        "omeprazole", "losartan", "gabapentin", "hydrochlorothiazide",
        "sertraline", "fluoxetine", "prednisone", "amoxicillin", "warfarin",
        "ibuprofen", "acetaminophen", "aspirin", "insulin", "levothyroxine",
        "alprazolam", "lorazepam", "oxycodone", "tramadol", "morphine",
        "alendronate", "escitalopram", "tiotropium", "enalapril", "levothyroxine",
        "hydrocodone"
    ]

    def __init__(self):
        self._symptom_patterns = self._build_symptom_patterns()
        self._drug_patterns = self._build_drug_patterns()
        self._disease_patterns = self._build_disease_patterns()

    def _build_symptom_patterns(self) -> re.Pattern:
        symptom_names = "|".join(re.escape(s) for s in self.KNOWN_SYMPTOMS)
        patterns = [
            rf"\b(?:what are |show me |list |find |get )?(?:the )?(?:symptoms?|signs?|manifestations?)\b",
            rf"\b(?:symptoms?|signs?|manifestations?)\b",
            rf"\b{self._join_words(self.SYMPTOM_WORDS)}\b",
        ]
        symptom_clause = "|".join(patterns)
        name_clause = rf"(?:of|for|in|with) (?:the )?({symptom_names})"
        pattern = rf"{symptom_clause}[^\w]*{name_clause}|{name_clause}[^\w]*{symptom_clause}"
        return re.compile(pattern, re.IGNORECASE)

    def _build_drug_patterns(self) -> re.Pattern:
        drug_names = "|".join(re.escape(d) for d in self.KNOWN_DRUGS)
        patterns = [
            rf"\b(?:interactions?|interact|combine|with)\b[^\w]*({drug_names})",
            rf"({drug_names})[^\w]*(?:interactions?|interact|combine|with)\b",
            rf"\b({drug_names})\b.*\b({drug_names})\b",
        ]
        return re.compile("|".join(patterns), re.IGNORECASE)

    def _build_disease_patterns(self) -> re.Pattern:
        disease_names = "|".join(re.escape(d) for d in self.KNOWN_DISEASES)
        return re.compile(disease_names, re.IGNORECASE)

    def _join_words(self, words: List[str]) -> str:
        return "|".join(re.escape(w) for w in words)

    def detect_intent(self, query: str) -> Tuple[Intent, List[Entity]]:
        query_lower = query.lower().strip()

        entities = self.extract_entities(query)

        # Drug interaction: two drugs mentioned
        if self._detect_interaction_intent(query_lower):
            drug_entities = [e for e in entities if e.type == "drug"]
            if len(drug_entities) >= 2:
                return Intent.DRUG_INTERACTIONS, drug_entities[:2]
            if len(drug_entities) == 1:
                return Intent.DRUG_INTERACTIONS, drug_entities

        # Get symptoms of disease (MUST check before symptom-only checks)
        if self._detect_symptom_intent(query_lower):
            disease_entities = [e for e in entities if e.type == "disease"]
            if disease_entities:
                return Intent.GET_SYMPTOMS, disease_entities
            # Check if query contains known disease
            disease_name = self._extract_disease_name(query_lower)
            if disease_name:
                return Intent.GET_SYMPTOMS, [Entity(type="disease", value=disease_name, original=disease_name)]
            # If just asking about symptoms without a disease, might be find_diseases
            symptom_entities = [e for e in entities if e.type == "symptom"]
            if symptom_entities and self._detect_find_disease_intent(query_lower):
                return Intent.FIND_DISEASES, symptom_entities

        # Get treatments of disease
        if self._detect_treatment_intent(query_lower):
            disease_entities = [e for e in entities if e.type == "disease"]
            if disease_entities:
                return Intent.GET_TREATMENTS, disease_entities
            disease_name = self._extract_disease_name(query_lower)
            if disease_name:
                return Intent.GET_TREATMENTS, [Entity(type="disease", value=disease_name, original=disease_name)]

        # Predict disease: multiple symptoms + prediction keywords
        symptom_entities = [e for e in entities if e.type == "symptom"]
        if self._detect_predict_intent(query_lower) and len(symptom_entities) >= 1:
            return Intent.PREDICT_DISEASE, symptom_entities

        # Find diseases by symptom
        if symptom_entities and self._detect_find_disease_intent(query_lower):
            return Intent.FIND_DISEASES, symptom_entities

        # Get disease info
        if self._detect_info_intent(query_lower):
            disease_entities = [e for e in entities if e.type == "disease"]
            if disease_entities:
                return Intent.GET_INFO, disease_entities
            disease_name = self._extract_disease_name(query_lower)
            if disease_name:
                return Intent.GET_INFO, [Entity(type="disease", value=disease_name, original=disease_name)]

        # Find related diseases
        if self._detect_related_intent(query_lower):
            disease_entities = [e for e in entities if e.type == "disease"]
            if disease_entities:
                return Intent.FIND_RELATED, disease_entities
            disease_name = self._extract_disease_name(query_lower)
            if disease_name:
                return Intent.FIND_RELATED, [Entity(type="disease", value=disease_name, original=disease_name)]

        # Search intent: generic search
        if self._detect_search_intent(query_lower):
            return Intent.SEARCH, entities

        return Intent.UNKNOWN, entities

    def _detect_symptom_intent(self, query: str) -> bool:
        patterns = [
            r"symptoms?",
            r"signs?",
            r"manifestations?",
            r"what are the symptoms of",
            r"show me symptoms",
            r"get symptoms",
            r"symptoms of",
            r"signs of",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_treatment_intent(self, query: str) -> bool:
        patterns = [
            r"treatment",
            r"therapy",
            r"treated",
            r"treatments?",
            r"medication",
            r"medications?",
            r"drug",
            r"cure",
            r"managing",
            r"how is .* treated",
            r"treated by",
            r"treatments for",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_predict_intent(self, query: str) -> bool:
        patterns = [
            r"predict",
            r"diagnos",
            r"could.*be",
            r"might.*be",
            r"likely",
            r"possible",
            r"what disease.*could",
            r"what condition.*could",
            r"caused by",
            r"patient.*with",
            r"symptoms:",
            r"i have.*and.*what could",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_interaction_intent(self, query: str) -> bool:
        patterns = [
            r"interact",
            r"interaction",
            r"combine",
            r"with .* and",
            r"alongside",
            r"concurrently",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_find_disease_intent(self, query: str) -> bool:
        patterns = [
            r"find.*disease",
            r"disease.*symptom",
            r"which disease",
            r"what disease",
            r"diseases.*with",
            r"what diseases cause",
            r"diseases cause",
            r"cause.*fever",
            r"cause.*symptom",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_info_intent(self, query: str) -> bool:
        patterns = [
            r"info",
            r"information",
            r"about",
            r"details",
            r"what is",
            r"tell me about",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_related_intent(self, query: str) -> bool:
        patterns = [
            r"related",
            r"similar",
            r"like .* disease",
            r"associated",
            r"connected",
        ]
        return any(re.search(p, query) for p in patterns)

    def _detect_search_intent(self, query: str) -> bool:
        return len(query.strip()) > 2

    def extract_entities(self, query: str) -> List[Entity]:
        entities = []
        query_lower = query.lower()

        # Extract symptoms
        for symptom in self.KNOWN_SYMPTOMS:
            if symptom in query_lower:
                entities.append(Entity(type="symptom", value=symptom, original=symptom))

        # Extract drugs
        for drug in self.KNOWN_DRUGS:
            if drug in query_lower:
                entities.append(Entity(type="drug", value=drug, original=drug))

        # Extract diseases
        disease_name = self._extract_disease_name(query_lower)
        if disease_name:
            entities.append(Entity(type="disease", value=disease_name, original=disease_name))

        # Deduplicate by type
        seen = set()
        deduped = []
        for e in entities:
            if e.type not in seen:
                seen.add(e.type)
                deduped.append(e)

        return deduped

    def _extract_disease_name(self, query: str) -> Optional[str]:
        # Check known diseases
        for disease in self.KNOWN_DISEASES:
            if disease in query:
                return disease.title()

        # Try to extract pattern: "disease of X" or "X disease"
        patterns = [
            r"(\w+)\s+disease",
            r"(\w+)\s+syndrome",
            r"(\w+)\s+disorder",
            r"disease\s+(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).title()

        return None

    def parse(self, query: str) -> ParsedQuery:
        intent, entities = self.detect_intent(query)
        return ParsedQuery(
            intent=intent,
            entities=entities,
            raw_query=query
        )


# Global instance
_nlp_processor: Optional[NLPProcessor] = None


def get_nlp_processor() -> NLPProcessor:
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor
