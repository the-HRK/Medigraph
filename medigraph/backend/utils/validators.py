"""
Validators Module
Input validation utilities
"""
import re
from typing import List, Optional


def validate_disease_name(name: str) -> bool:
    """Validate disease name format."""
    if not name or len(name) < 2:
        return False
    # Allow letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']+$"
    return bool(re.match(pattern, name))


def validate_symptom_name(name: str) -> bool:
    """Validate symptom name format."""
    if not name or len(name) < 2:
        return False
    pattern = r"^[a-zA-Z\s\-']+$"
    return bool(re.match(pattern, name))


def validate_drug_name(name: str) -> bool:
    """Validate drug name format."""
    if not name or len(name) < 2:
        return False
    pattern = r"^[a-zA-Z0-9\s\-']+$"
    return bool(re.match(pattern, name))


def sanitize_search_term(term: str) -> str:
    """Sanitize user search input."""
    if not term:
        return ""
    # Remove special characters, keep alphanumeric and spaces
    sanitized = re.sub(r"[^\w\s\-']", "", term)
    return sanitized.strip()[:100]


def validate_symptoms_list(symptoms: List[str]) -> List[str]:
    """Validate and filter symptoms list."""
    if not symptoms:
        return []
    validated = []
    for symptom in symptoms[:10]:  # Limit to 10 symptoms
        if validate_symptom_name(symptom):
            validated.append(symptom.title())
    return validated
