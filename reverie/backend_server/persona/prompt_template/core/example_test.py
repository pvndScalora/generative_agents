"""
Simple test example to verify the new prompt infrastructure works.

This creates a WakeUpHourPrompt to test the BasePrompt and PromptExecutor.
Run this manually to verify everything is working before migrating all prompts.
"""

from typing import Optional
from pydantic import BaseModel, Field
from .base import BasePrompt
from .executor import PromptExecutor


# Define input schema
class WakeUpHourInput(BaseModel):
    """Input data for wake up hour prediction."""
    identity_stable_set: str = Field(..., description="Persona's core identity and traits")
    lifestyle: str = Field(..., description="Lifestyle description including sleep habits")
    first_name: str = Field(..., description="First name of the persona")


# Define output schema
class WakeUpHourOutput(BaseModel):
    """Structured output for wake up hour."""
    hour: int = Field(..., ge=0, le=23, description="Wake up hour (0-23)")
    reasoning: Optional[str] = Field(None, description="Brief reasoning for this hour")


# Implement the prompt
class WakeUpHourPrompt(BasePrompt[WakeUpHourInput, WakeUpHourOutput]):
    """Prompt to determine a persona's wake up hour."""

    input_schema = WakeUpHourInput
    output_schema = WakeUpHourOutput

    def render_prompt(self, input_data: WakeUpHourInput) -> str:
        """Render the prompt text using f-strings."""
        return f"""{input_data.identity_stable_set}

In general, {input_data.lifestyle}

{input_data.first_name}'s wake up hour:"""

    def get_fail_safe(self) -> WakeUpHourOutput:
        """Return safe default (8 AM)."""
        return WakeUpHourOutput(hour=8, reasoning="Default wake up time")


# Example usage (commented out - uncomment to test manually)
"""
if __name__ == "__main__":
    # This is how you would use the new system:
    from reverie.backend_server.infra.llm.service import LLMService
    from reverie.backend_server.infra.llm.providers.openai import OpenAIProvider

    # Setup (you would get this from your existing setup)
    provider = OpenAIProvider(api_key="your-api-key")
    llm_service = LLMService(provider)
    executor = PromptExecutor(llm_service)

    # Create input data (type-safe!)
    input_data = WakeUpHourInput(
        identity_stable_set="Klaus Mueller is a student at Oak Hill College studying sociology.",
        lifestyle="Klaus goes to bed around 11pm and is an early riser who likes to have breakfast before class.",
        first_name="Klaus"
    )

    # Execute prompt
    prompt = WakeUpHourPrompt()
    result = executor.execute(prompt, input_data, temperature=0.8)

    # Use the result (type-safe!)
    print(f"Wake up hour: {result.hour}")
    print(f"Reasoning: {result.reasoning}")

    # IDE autocomplete works!
    # result.hour (autocompletes)
    # result.reasoning (autocompletes)
"""
