from dataclasses import dataclass
from typing import Dict
import threading

@dataclass
class ModelCost:
    input_cost_per_1k: float
    output_cost_per_1k: float

# Pricing as of late 2023 (can be updated)
MODEL_PRICING = {
    "gpt-3.5-turbo": ModelCost(0.0015, 0.002),
    "gpt-4": ModelCost(0.03, 0.06),
    "text-embedding-ada-002": ModelCost(0.0001, 0.0),
}

class CostTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CostTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.total_tokens = 0
        self.total_cost = 0.0
        self.model_usage: Dict[str, Dict[str, int]] = {}
        self._initialized = True

    def update(self, model: str, prompt_tokens: int, completion_tokens: int):
        with self._lock:
            self.total_tokens += (prompt_tokens + completion_tokens)
            
            if model not in self.model_usage:
                self.model_usage[model] = {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
            
            self.model_usage[model]["prompt_tokens"] += prompt_tokens
            self.model_usage[model]["completion_tokens"] += completion_tokens
            
            cost = 0.0
            # Handle model versions (e.g., gpt-4-0613 -> gpt-4)
            base_model = next((m for m in MODEL_PRICING if model.startswith(m)), None)
            
            if base_model:
                pricing = MODEL_PRICING[base_model]
                cost = (prompt_tokens / 1000 * pricing.input_cost_per_1k) + \
                       (completion_tokens / 1000 * pricing.output_cost_per_1k)
            
            self.model_usage[model]["cost"] += cost
            self.total_cost += cost

    def get_report(self) -> Dict:
        with self._lock:
            return {
                "total_tokens": self.total_tokens,
                "total_cost": round(self.total_cost, 4),
                "breakdown": self.model_usage
            }

    def reset(self):
        with self._lock:
            self.total_tokens = 0
            self.total_cost = 0.0
            self.model_usage = {}
