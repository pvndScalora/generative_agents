from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers (e.g., OpenAI, Anthropic, Local).
    """

    @abstractmethod
    def chat_completion(self, 
                        model: str, 
                        messages: List[Dict[str, str]], 
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> Tuple[str, Dict[str, int]]:
        """
        Execute a chat completion request.
        
        Returns:
            Tuple[str, Dict[str, int]]: The response content and usage statistics.
            Usage dict should contain keys like 'prompt_tokens', 'completion_tokens'.
        """
        pass

    @abstractmethod
    def completion(self, 
                   model: str, 
                   prompt: str, 
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None,
                   **kwargs) -> Tuple[str, Dict[str, int]]:
        """
        Execute a text completion request (legacy).
        
        Returns:
            Tuple[str, Dict[str, int]]: The response content and usage statistics.
        """
        pass

    @abstractmethod
    def embedding(self, 
                  text: Union[str, List[str]], 
                  model: str) -> Tuple[Union[List[float], List[List[float]]], Dict[str, int]]:
        """
        Get embeddings for text.
        
        Returns:
            Tuple[Union[List[float], List[List[float]]], Dict[str, int]]: The embeddings and usage statistics.
        """
        pass
