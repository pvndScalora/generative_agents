"""
Prompt executor with structured JSON output using Pydantic validation.

This module replaces the old string-parsing approach with type-safe
structured outputs validated by Pydantic schemas.
"""

import json
import logging
from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel, ValidationError

from infra.llm.service import LLMService
from .base import BasePrompt, TInput, TOutput


logger = logging.getLogger(__name__)


class PromptExecutor:
    """
    Executes prompts with structured JSON output and Pydantic validation.

    This replaces the old executor that used string parsing and positional
    inputs. The new approach:
    1. Takes structured Pydantic input models
    2. Renders prompts using f-strings
    3. Requests JSON output from the LLM
    4. Validates output with Pydantic schemas
    5. Returns type-safe structured data
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize the executor.

        Args:
            llm_service: The LLM service for making API calls
        """
        self.llm_service = llm_service

    def execute(
        self,
        prompt: BasePrompt[TInput, TOutput],
        input_data: TInput,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        **kwargs
    ) -> TOutput:
        """
        Execute a prompt with structured input and output.

        Args:
            prompt: The prompt instance to execute
            input_data: Validated Pydantic input model
            model: The LLM model to use
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            max_retries: Number of validation retries
            **kwargs: Additional arguments for the LLM provider

        Returns:
            Validated output model instance

        Raises:
            ValueError: If input validation fails
            Exception: If LLM service fails after all retries
        """
        # Validate input (beyond Pydantic schema validation)
        try:
            prompt.validate_input(input_data)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            raise

        # Render the prompt text
        prompt_text = prompt.render_prompt(input_data)

        # Build messages with JSON schema instruction
        messages = self._build_messages(prompt_text, prompt.output_schema)

        # Execute with retries and validation
        for attempt in range(max_retries):
            try:
                # Request JSON output
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},  # JSON mode
                    **kwargs
                )

                # Parse and validate JSON
                output = self._parse_and_validate(
                    response_content,
                    prompt.output_schema
                )

                # Post-process if needed
                output = prompt.post_process(output, input_data)

                logger.debug(f"Prompt executed successfully on attempt {attempt + 1}")
                return output

            except ValidationError as e:
                logger.warning(
                    f"Validation failed on attempt {attempt + 1}/{max_retries}: {e}"
                )
                if attempt == max_retries - 1:
                    # Final retry failed, return fail-safe
                    logger.error("All retries exhausted, returning fail-safe")
                    return prompt.get_fail_safe()
                continue

            except json.JSONDecodeError as e:
                logger.warning(
                    f"JSON parsing failed on attempt {attempt + 1}/{max_retries}: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error("All retries exhausted, returning fail-safe")
                    return prompt.get_fail_safe()
                continue

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return prompt.get_fail_safe()
                continue

        # Should never reach here, but just in case
        return prompt.get_fail_safe()

    def _build_messages(
        self,
        prompt_text: str,
        output_schema: type[BaseModel]
    ) -> list[Dict[str, str]]:
        """
        Build chat messages with JSON schema instruction.

        Args:
            prompt_text: The rendered prompt text
            output_schema: The Pydantic model for the output

        Returns:
            List of message dictionaries for the chat API
        """
        # Get JSON schema from Pydantic model
        schema = output_schema.model_json_schema()

        # Remove unnecessary schema metadata for cleaner prompt
        schema_clean = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }

        # System message with JSON schema
        system_content = (
            "You are a helpful assistant that generates JSON responses. "
            "You must respond with valid JSON that matches the following schema:\n\n"
            f"{json.dumps(schema_clean, indent=2)}\n\n"
            "Do not include any text outside the JSON object."
        )

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt_text}
        ]

    def _parse_and_validate(
        self,
        response_content: str,
        output_schema: type[BaseModel]
    ) -> BaseModel:
        """
        Parse JSON and validate with Pydantic schema.

        Args:
            response_content: Raw LLM response
            output_schema: Pydantic model class for validation

        Returns:
            Validated model instance

        Raises:
            json.JSONDecodeError: If JSON parsing fails
            ValidationError: If Pydantic validation fails
        """
        # Try to extract JSON if wrapped in markdown code blocks
        response_content = response_content.strip()

        # Remove markdown code fences if present
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        elif response_content.startswith("```"):
            response_content = response_content[3:]

        if response_content.endswith("```"):
            response_content = response_content[:-3]

        response_content = response_content.strip()

        # Parse JSON
        try:
            data = json.loads(response_content)
        except json.JSONDecodeError:
            # Try to find JSON object boundaries
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(response_content[start:end])
            else:
                raise

        # Validate with Pydantic
        return output_schema.model_validate(data)
