import time
import logging
from typing import List, Dict, Any, Optional, Union
from .interfaces import LLMProvider
from .cost_tracker import CostTracker
from .errors import LLMRetryableError, LLMFatalError

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    """
    Service layer for LLM interactions.
    Handles:
    - Provider abstraction
    - Retry logic
    - Cost tracking
    """
    def __init__(self, provider: LLMProvider, max_retries: int = 3, retry_delay: float = 1.0):
        self.provider = provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cost_tracker = CostTracker()

    def chat_completion(self, 
                        model: str, 
                        messages: List[Dict[str, str]], 
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> str:
        """
        Execute a chat completion request with retry logic and cost tracking.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                content, usage = self.provider.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Track usage
                self.cost_tracker.update(
                    model=model,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0)
                )
                
                return content

            except LLMRetryableError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"LLM request failed after {self.max_retries} retries: {e}")
                    raise e
                
                sleep_time = self.retry_delay * (2 ** (retries - 1)) # Exponential backoff
                logger.warning(f"LLM request failed ({e}). Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}")
                raise e

    def completion(self, 
                   model: str, 
                   prompt: str, 
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None,
                   **kwargs) -> str:
        """
        Execute a text completion request with retry logic and cost tracking.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                content, usage = self.provider.completion(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Track usage
                self.cost_tracker.update(
                    model=model,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0)
                )
                
                return content

            except LLMRetryableError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"LLM request failed after {self.max_retries} retries: {e}")
                    raise e
                
                sleep_time = self.retry_delay * (2 ** (retries - 1)) # Exponential backoff
                logger.warning(f"LLM request failed ({e}). Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}")
                raise e

    def embedding(self, text: Union[str, List[str]], model: str = "text-embedding-ada-002") -> Union[List[float], List[List[float]]]:
        """
        Get embeddings for text.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                embeddings, usage = self.provider.embedding(
                    text=text,
                    model=model
                )
                
                # Track usage
                self.cost_tracker.update(
                    model=model,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=0
                )
                
                return embeddings

            except LLMRetryableError as e:
                retries += 1
                if retries > self.max_retries:
                    raise e
                time.sleep(self.retry_delay * (2 ** (retries - 1)))
