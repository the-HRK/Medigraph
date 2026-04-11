"""
Utilities Module
Common helper functions
"""
from typing import Any, Dict, List, Optional


def safe_get(dictionary: Dict, *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result


def format_results(results: List[Dict], limit: int = 10) -> List[Dict]:
    """Format database results for API response."""
    return results[:limit] if results else []


def extract_names(results: List[Dict], key: str = "name") -> List[str]:
    """Extract name field from list of result dicts."""
    return [r.get(key, "") for r in results if r.get(key)]


def paginate_results(results: List[Any], page: int = 1, page_size: int = 20) -> Dict:
    """Paginate a list of results."""
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "data": results[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }
