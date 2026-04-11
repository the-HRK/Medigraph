"""
LLM Integration Service
Provides optional LLM-powered response enhancement
Works with Ollama or OpenAI while grounding responses in graph data
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import os
import json


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    NONE = "none"


@dataclass
class LLMConfig:
    provider: LLMProvider = LLMProvider.NONE
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "llama3"
    temperature: float = 0.3  # Low temp to reduce hallucination
    max_tokens: int = 500
    enabled: bool = False


@dataclass
class LLMResponse:
    enhanced_text: str
    confidence_modifier: float = 0.0  # Can adjust confidence based on LLM quality
    sources_used: List[str] = None

    def __post_init__(self):
        if self.sources_used is None:
            self.sources_used = []


class LLMService:
    """
    Optional LLM integration for Medigraph chatbot.

    Supports:
    - Ollama (local models)
    - OpenAI (API models)

    Key design: Always grounds responses in the graph data provided.
    LLM is only used to naturalize the text, not to invent facts.
    """

    SYSTEM_PROMPT = """You are Medigraph, a medical knowledge graph assistant.
You help users understand medical information from a healthcare knowledge graph database.

IMPORTANT RULES:
1. ONLY use information provided in the "Graph Data" section
2. Do NOT invent, assume, or hallucinate any medical facts
3. If the graph data is incomplete, say so clearly
4. Convert the structured data into natural, conversational responses
5. Explain your reasoning when needed
6. Be clear and concise
7. If you don't know something based on the data, say "I don't have that information"

User will provide graph data. Respond naturally."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_config_from_env()
        self._client = None

    def _load_config_from_env(self) -> LLMConfig:
        """Load LLM configuration from environment variables."""
        provider_str = os.getenv("LLM_PROVIDER", "none").lower()

        if provider_str == "ollama":
            return LLMConfig(
                provider=LLMProvider.OLLAMA,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "llama3"),
                enabled=True
            )
        elif provider_str == "openai":
            return LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                enabled=True
            )
        else:
            return LLMConfig(provider=LLMProvider.NONE, enabled=False)

    def is_enabled(self) -> bool:
        """Check if LLM enhancement is enabled."""
        return self.config.enabled and self.config.provider != LLMProvider.NONE

    def _get_client(self):
        """Lazy-load the appropriate HTTP client."""
        if self._client is not None:
            return self._client

        if self.config.provider == LLMProvider.OLLAMA:
            try:
                import httpx
                self._client = httpx.Client(
                    base_url=self.config.base_url,
                    timeout=60.0
                )
                return self._client
            except ImportError:
                return None

        elif self.config.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    timeout=60.0
                )
                return self._client
            except ImportError:
                return None

        return None

    def enhance_response(
        self,
        graph_data: Dict[str, Any],
        original_response: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Use LLM to enhance a response while grounding in graph data.

        Args:
            graph_data: The structured data from Neo4j
            original_response: The template-based response text
            intent: The detected intent type
            context: Optional conversation context

        Returns:
            LLMResponse with enhanced text
        """
        if not self.is_enabled():
            return LLMResponse(
                enhanced_text=original_response,
                confidence_modifier=0.0,
                sources_used=["template"]
            )

        # Build prompt with graph data
        prompt = self._build_enhancement_prompt(
            graph_data, original_response, intent, context
        )

        try:
            if self.config.provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt, original_response)
            elif self.config.provider == LLMProvider.OPENAI:
                return self._call_openai(prompt, original_response)
        except Exception as e:
            # On LLM failure, fall back to template response
            return LLMResponse(
                enhanced_text=original_response,
                confidence_modifier=-0.1,  # Slightly penalize confidence
                sources_used=["template", f"llm_error:{str(e)[:50]}"]
            )

        return LLMResponse(
            enhanced_text=original_response,
            sources_used=["template"]
        )

    def _build_enhancement_prompt(
        self,
        graph_data: Dict[str, Any],
        original_response: str,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt that guides LLM to enhance without hallucinating."""
        graph_json = json.dumps(graph_data, indent=2, default=str)

        intent_guide = {
            "get_symptoms": "The user asked about symptoms of a disease. Naturalize the symptom list.",
            "get_treatments": "The user asked about treatments. Present the treatments naturally.",
            "find_diseases": "The user wants to find diseases by symptom. List the matching diseases.",
            "drug_interactions": "The user asked about drug interactions. Be clear about any interactions found.",
            "predict_disease": "The user provided symptoms for disease prediction. Present possible conditions.",
            "get_info": "The user wants disease information. Provide a natural summary.",
            "find_related": "The user asked for related diseases. List the related conditions.",
            "search": "The user performed a search. Present search results naturally."
        }.get(intent, "Respond to the user's query.")

        context_section = ""
        if context:
            if context.get("last_disease"):
                context_section += f"\n- Previously discussed disease: {context['last_disease']}"
            if context.get("last_symptoms"):
                context_section += f"\n- Previously mentioned symptoms: {', '.join(context['last_symptoms'])}"

        prompt = f"""Graph Data:
{graph_json}

Original Response:
{original_response}

Intent: {intent}
{intent_guide}

{context_section}

Provide an enhanced but factual response based ONLY on the graph data above.
Keep it conversational and easy to understand.
If data is limited, work with what you have - don't make up information."""

        return prompt

    def _call_ollama(self, prompt: str, fallback: str) -> LLMResponse:
        """Call Ollama API."""
        client = self._get_client()
        if not client:
            return LLMResponse(enhanced_text=fallback, sources_used=["template"])

        try:
            response = client.post(
                "/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "system": self.SYSTEM_PROMPT,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return LLMResponse(
                enhanced_text=result.get("response", fallback),
                confidence_modifier=0.05,  # LLM adds some confidence
                sources_used=["ollama", self.config.model]
            )
        except Exception as e:
            return LLMResponse(
                enhanced_text=fallback,
                sources_used=["template", f"ollama_error:{str(e)[:30]}"]
            )

    def _call_openai(self, prompt: str, fallback: str) -> LLMResponse:
        """Call OpenAI API."""
        client = self._get_client()
        if not client:
            return LLMResponse(enhanced_text=fallback, sources_used=["template"])

        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return LLMResponse(
                enhanced_text=response.choices[0].message.content,
                confidence_modifier=0.05,
                sources_used=["openai", self.config.model]
            )
        except Exception as e:
            return LLMResponse(
                enhanced_text=fallback,
                sources_used=["template", f"openai_error:{str(e)[:30]}"]
            )

    def check_health(self) -> Dict[str, Any]:
        """Check if LLM service is available."""
        if not self.is_enabled():
            return {"available": False, "reason": "LLM not enabled"}

        if self.config.provider == LLMProvider.OLLAMA:
            try:
                client = self._get_client()
                if not client:
                    return {"available": False, "reason": "httpx not installed"}
                response = client.get("/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {
                        "available": True,
                        "provider": "ollama",
                        "available_models": [m["name"] for m in models]
                    }
                return {"available": False, "reason": f"Status: {response.status_code}"}
            except Exception as e:
                return {"available": False, "reason": str(e)}

        elif self.config.provider == LLMProvider.OPENAI:
            try:
                client = self._get_client()
                if not client:
                    return {"available": False, "reason": "openai not installed"}
                # Just verify API key works
                client.models.list()
                return {"available": True, "provider": "openai", "model": self.config.model}
            except Exception as e:
                return {"available": False, "reason": str(e)}

        return {"available": False, "reason": "Unknown provider"}


# Global instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def is_llm_available() -> bool:
    return get_llm_service().is_enabled()
