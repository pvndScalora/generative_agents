"""
Base prompt class for type-safe prompt execution.

This module provides the foundation for the new Pydantic-based prompt system,
replacing the old string-parsing approach with structured inputs and outputs.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type
from pydantic import BaseModel


# Type variables for input and output schemas
TInput = TypeVar('TInput', bound=BaseModel)
TOutput = TypeVar('TOutput', bound=BaseModel)


class BasePrompt(ABC, Generic[TInput, TOutput]):
    """
    Base class for all prompts with type-safe inputs and outputs.

    This replaces the old BasePrompt class that used positional list inputs
    and brittle string parsing for outputs.

    Example:
        class WakeUpHourInput(BaseModel):
            identity_stable_set: str
            lifestyle: str
            first_name: str

        class WakeUpHourOutput(BaseModel):
            hour: int = Field(..., ge=4, le=11)
            reasoning: Optional[str] = None

        class WakeUpHourPrompt(BasePrompt[WakeUpHourInput, WakeUpHourOutput]):
            input_schema = WakeUpHourInput
            output_schema = WakeUpHourOutput

            def render_prompt(self, input_data: WakeUpHourInput) -> str:
                return f"{input_data.identity_stable_set}\\n\\n" \
                       f"In general, {input_data.lifestyle}\\n\\n" \
                       f"{input_data.first_name}'s wake up hour:"

            def get_fail_safe(self) -> WakeUpHourOutput:
                return WakeUpHourOutput(hour=8, reasoning="Default")
    """

    # Subclasses must define these
    input_schema: Type[TInput]
    output_schema: Type[TOutput]

    @abstractmethod
    def render_prompt(self, input_data: TInput) -> str:
        """
        Render the prompt text using the input data.

        This method should use f-strings to create the prompt text from the
        structured input data. The template is inline in the code, providing
        IDE autocomplete and type checking.

        Args:
            input_data: Validated Pydantic model containing all prompt inputs

        Returns:
            The rendered prompt text ready to send to the LLM
        """
        pass

    @abstractmethod
    def get_fail_safe(self) -> TOutput:
        """
        Return a safe default output when LLM execution fails.

        This is called after all retries are exhausted. It should return
        a sensible default that won't crash downstream code.

        Returns:
            A valid instance of the output schema with safe default values
        """
        pass

    def validate_input(self, input_data: TInput) -> None:
        """
        Additional input validation beyond Pydantic schema validation.

        Override this method if you need custom validation logic.
        Raise ValueError with a descriptive message if validation fails.

        Args:
            input_data: The input data to validate

        Raises:
            ValueError: If validation fails
        """
        pass

    def post_process(self, output: TOutput, input_data: TInput) -> TOutput:
        """
        Post-process the LLM output before returning.

        Override this method if you need to adjust or normalize the output.
        This can be used to implement legacy behavior like duration normalization.

        Args:
            output: The validated output from the LLM
            input_data: The original input data (for context)

        Returns:
            The processed output
        """
        return output
