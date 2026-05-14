"""
Pluggable Intelligence Providers for OBI 2.0.
Supports Regex (Fast/Free), Ollama (Local LLM), and potentially Cloud APIs.
"""
import json
import re
import requests

class BaseProvider:
    def analyze_signals(self, text):
        raise NotImplementedError

class RegexProvider(BaseProvider):
    """
    Primary Deterministic Provider. 
    Budget docs are structured legal instruments; regex should be the main play.
    """
    def __init__(self):
        # Austerity signals: Spending cuts, service freezes, and labor precarity
        self.austerity_markers = [
            r"rationalization", r"freeze", r"expenditure control", r"merger of schemes",
            r"austerity", r"cut", r"reduction", r"efficiency", r"disinvestment",
            r"contractual cadre", r"honorarium", r"fixed term", r"outsource"
        ]
        # Extravagance signals: Capital subsidies and asset-inflation incentives
        self.extravagance_markers = [
            r"concession", r"incentive", r"investor", r"viability gap", r"ppp",
            r"exemption", r"tax holiday", r"subsidy to capital", r"asset inflation",
            r"mega project", r"mou signed", r"global summit"
        ]
        # Unit Discipline signals: To ensure deterministic accounting
        self.unit_markers = [
            r"lakh crore", r"rs\. in cr", r"₹ in cr", r"in thousand"
        ]

    def _count(self, text, markers):
        count = 0
        text_lower = text.lower()
        for marker in markers:
            count += len(re.findall(marker, text_lower))
        return count

    def analyze_signals(self, text):
        return {
            "austerity_score": self._count(text, self.austerity_markers),
            "extravagance_score": self._count(text, self.extravagance_markers),
            "provider": "regex"
        }

class OllamaProvider(BaseProvider):
    """Local LLM provider using Ollama (e.g. Llama3, Mistral)."""
    def __init__(self, model="llama3", url="http://localhost:11434/api/generate"):
        self.model = model
        self.url = url

    def analyze_signals(self, text):
        # We only send a sample to stay within local context limits
        sample = text[:2000]
        prompt = f"""
        Analyze the following budget text using the Melinda Cooper framework.
        Identify signals of:
        1. 'Austerity' (spending cuts, service freezes, rationalization).
        2. 'Extravagance' (capital subsidies, investor incentives, concessions).
        
        Return ONLY a JSON object with two integer scores (0-10) for each category.
        Format: {{"austerity_score": int, "extravagance_score": int}}
        
        TEXT:
        {sample}
        """
        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=30)
            result = response.json()
            data = json.loads(result['response'])
            data["provider"] = f"ollama:{self.model}"
            return data
        except Exception as e:
            return {"error": str(e), "austerity_score": 0, "extravagance_score": 0, "provider": "ollama:error"}

def get_provider(provider_type, **kwargs):
    if provider_type == "ollama":
        return OllamaProvider(**kwargs)
    return RegexProvider()
