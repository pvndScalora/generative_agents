import openai
from typing import List, Dict, Any, Optional, Union, Tuple
from ..interfaces import LLMProvider
from ..errors import LLMRetryableError, LLMFatalError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def chat_completion(self, 
                        model: str, 
                        messages: List[Dict[str, str]], 
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> Tuple[str, Dict[str, int]]:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            return content, usage

        except (openai.error.RateLimitError, 
                openai.error.APIError, 
                openai.error.Timeout, 
                openai.error.ServiceUnavailableError) as e:
            raise LLMRetryableError(f"OpenAI Retryable Error: {e}") from e
        except Exception as e:
            raise LLMFatalError(f"OpenAI Fatal Error: {e}") from e

    def completion(self, 
                   model: str, 
                   prompt: str, 
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None,
                   **kwargs) -> Tuple[str, Dict[str, int]]:
        try:
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].text
            usage = response.get("usage", {})
            return content, usage

        except (openai.error.RateLimitError, 
                openai.error.APIError, 
                openai.error.Timeout, 
                openai.error.ServiceUnavailableError) as e:
            raise LLMRetryableError(f"OpenAI Retryable Error: {e}") from e
        except Exception as e:
            raise LLMFatalError(f"OpenAI Fatal Error: {e}") from e

    def embedding(self, 
                  text: Union[str, List[str]], 
                  model: str) -> Tuple[Union[List[float], List[List[float]]], Dict[str, int]]:
        try:
            response = openai.Embedding.create(
                input=text,
                model=model
            )
            
            data = response["data"]
            usage = response.get("usage", {})
            
            if isinstance(text, str):
                return data[0]["embedding"], usage
            return [item["embedding"] for item in data], usage

        except (openai.error.RateLimitError, 
                openai.error.APIError, 
                openai.error.Timeout, 
                openai.error.ServiceUnavailableError) as e:
            raise LLMRetryableError(f"OpenAI Retryable Error: {e}") from e
        except Exception as e:
            raise LLMFatalError(f"OpenAI Fatal Error: {e}") from e
