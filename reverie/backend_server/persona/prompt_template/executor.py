import json
import logging
from typing import Any, Dict, List, Optional, Union

from reverie.backend_server.infra.llm import LLMService
from reverie.backend_server.persona.prompt_template.prompts import BasePrompt

logger = logging.getLogger(__name__)

class PromptExecutor:
    """
    Executes prompts using the LLMService, handling prompt generation,
    execution, validation, and cleanup.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, 
                prompt: BasePrompt, 
                test_input: Any = None, 
                model: str = "gpt-3.5-turbo",
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                max_retries: int = 3,
                **kwargs) -> Any:
        """
        Executes a prompt.

        Args:
            prompt: The prompt instance to execute.
            test_input: Optional input to override the prompt's default input generation.
            model: The LLM model to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            max_retries: Number of retries for validation failures.
            **kwargs: Additional arguments for the LLM provider.

        Returns:
            The processed output from the prompt.
        """
        
        # 1. Generate the prompt text
        prompt_text = self._generate_prompt_text(prompt, test_input)
        
        # 2. Determine execution mode (Chat vs Completion)
        # For now, we infer based on the presence of example_output/special_instruction
        # or if the model is a known chat model.
        
        is_chat_model = ("gpt-3.5" in model or "gpt-4" in model) and "instruct" not in model
        
        # If the prompt has specific instructions for JSON output, we might want to wrap it
        if prompt.example_output is not None and prompt.special_instruction is not None:
            return self._execute_chat_safe(
                prompt_text, 
                prompt, 
                model, 
                temperature, 
                max_tokens, 
                max_retries, 
                **kwargs
            )
        else:
            # Legacy completion or simple chat
            if is_chat_model:
                return self._execute_chat_simple(
                    prompt_text, 
                    prompt, 
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )
            else:
                return self._execute_completion(
                    prompt_text, 
                    prompt, 
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )

    def _generate_prompt_text(self, prompt_instance: BasePrompt, test_input: Any = None) -> str:
        """
        Generates the raw prompt text by filling in the template.
        """
        prompt_input = prompt_instance.create_prompt_input(test_input)
        
        # Logic adapted from gpt_structure.generate_prompt
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        # We assume prompt_template is a file path relative to the project root or current working dir
        # In the original code, it opens the file directly.
        # We might need to handle paths better.
        try:
            with open(prompt_instance.prompt_template, "r") as f:
                prompt_text = f.read()
        except FileNotFoundError:
            # Try prepending the project root or similar if needed
            # For now, assume the path is correct as per original code
            raise

        for count, i in enumerate(prompt_input):   
            prompt_text = prompt_text.replace(f"!<INPUT {count}>!", i)
        
        if "<commentblockmarker>###</commentblockmarker>" in prompt_text: 
            prompt_text = prompt_text.split("<commentblockmarker>###</commentblockmarker>")[1]
            
        return prompt_text.strip()

    def _execute_chat_safe(self, 
                           prompt_text: str, 
                           prompt_instance: BasePrompt, 
                           model: str, 
                           temperature: float, 
                           max_tokens: Optional[int], 
                           max_retries: int,
                           **kwargs) -> Any:
        
        # Construct the "safe" prompt wrapper (JSON enforcement)
        # This logic mimics ChatGPT_safe_generate_response
        wrapped_prompt = f'"""\n{prompt_text}\n"""\n'
        wrapped_prompt += f"Output the response to the prompt above in json. {prompt_instance.special_instruction}\n"
        wrapped_prompt += "Example output json:\n"
        wrapped_prompt += f'{{"output": "{str(prompt_instance.example_output)}"}}'

        messages = [{"role": "user", "content": wrapped_prompt}]

        for i in range(max_retries + 1):
            try:
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Parse JSON
                response_content = response_content.strip()
                # Attempt to extract JSON if it's wrapped in other text
                try:
                    end_index = response_content.rfind('}') + 1
                    if end_index > 0:
                        response_content = response_content[:end_index]
                    parsed_json = json.loads(response_content)
                    output = parsed_json["output"]
                except (json.JSONDecodeError, KeyError):
                    # If parsing fails, maybe the model just outputted the text?
                    # But the prompt explicitly asks for JSON.
                    # Let's try to validate the raw content if JSON fails? 
                    # Original code assumes it MUST be JSON.
                    output = response_content

                if prompt_instance.validate(output, prompt=wrapped_prompt):
                    return prompt_instance.clean_up(output, prompt=wrapped_prompt)
                
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()

    def _execute_chat_simple(self, 
                             prompt_text: str, 
                             prompt_instance: BasePrompt, 
                             model: str, 
                             temperature: float, 
                             max_tokens: Optional[int], 
                             max_retries: int,
                             **kwargs) -> Any:
        
        messages = [{"role": "user", "content": prompt_text}]

        for i in range(max_retries + 1):
            try:
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if prompt_instance.validate(response_content, prompt=prompt_text):
                    return prompt_instance.clean_up(response_content, prompt=prompt_text)
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
                
        return prompt_instance.get_fail_safe()

    def _execute_completion(self, 
                            prompt_text: str, 
                            prompt_instance: BasePrompt, 
                            model: str, 
                            temperature: float, 
                            max_tokens: Optional[int], 
                            max_retries: int,
                            **kwargs) -> Any:
        
        for i in range(max_retries + 1):
            try:
                # We need to access the provider directly or add completion to LLMService
                # LLMService currently only has chat_completion.
                # But the provider interface has completion.
                # Let's assume we can access provider or LLMService will be updated.
                # For now, I'll use self.llm_service.provider.completion if available
                
                if hasattr(self.llm_service.provider, 'completion'):
                    response_content, _ = self.llm_service.provider.completion(
                        model=model,
                        prompt=prompt_text,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    # Fallback to chat if completion not available?
                    # Or raise error.
                    raise NotImplementedError("Completion not supported by this service/provider")

                if prompt_instance.validate(response_content, prompt=prompt_text):
                    return prompt_instance.clean_up(response_content, prompt=prompt_text)
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()
