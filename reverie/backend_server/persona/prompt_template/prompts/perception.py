"""
Perception prompt implementations with f-string templates.

This module contains all perception-related prompts that help the persona:
- Generate emojis for actions
- Extract semantic triples from events
- Describe object states
- Rate the importance/poignancy of events, thoughts, and conversations
"""

from persona.prompt_template.core.base import BasePrompt
from persona.prompt_template.schemas.perception import (
    PronunciatioInput, PronunciatioOutput,
    EventTripleInput, EventTripleOutput,
    ActObjDescInput, ActObjDescOutput,
    ActObjEventTripleInput, ActObjEventTripleOutput,
    EventPoignancyInput, EventPoignancyOutput,
    ThoughtPoignancyInput, ThoughtPoignancyOutput,
    ChatPoignancyInput, ChatPoignancyOutput,
)


# ============================================================================
# 1. Pronunciatio Prompt (Emoji Generation)
# ============================================================================

class PronunciatioPrompt(BasePrompt[PronunciatioInput, PronunciatioOutput]):
    """Generates an emoji to represent an action."""

    input_schema = PronunciatioInput
    output_schema = PronunciatioOutput

    def render_prompt(self, input_data: PronunciatioInput) -> str:
        return f"""Convert an action description to an emoji (important: use two or less emojis).

Action description: {input_data.action_description}
Emoji:"""

    def get_fail_safe(self) -> PronunciatioOutput:
        return PronunciatioOutput(emoji="😋")


# ============================================================================
# 2. Event Triple Prompt (Subject-Predicate-Object Extraction)
# ============================================================================

class EventTriplePrompt(BasePrompt[EventTripleInput, EventTripleOutput]):
    """Extracts subject-predicate-object triple from an event description."""

    input_schema = EventTripleInput
    output_schema = EventTripleOutput

    def render_prompt(self, input_data: EventTripleInput) -> str:
        return f"""Task: Turn the input into (subject, predicate, object). Output ONLY the triple.

Input: Sam Johnson is eating breakfast.
Output: (Sam Johnson, eat, breakfast)
---
Input: Joon Park is brewing coffee.
Output: (Joon Park, brew, coffee)
---
Input: Jane Cook is sleeping.
Output: (Jane Cook, is, sleeping)
---
Input: Michael Bernstein is writing email on a computer.
Output: (Michael Bernstein, write, email)
---
Input: Percy Liang is teaching students in a classroom.
Output: (Percy Liang, teach, students)
---
Input: Merrie Morris is running on a treadmill.
Output: (Merrie Morris, run, treadmill)
---
Input: {input_data.persona_name} is {input_data.action_description}.
Output:"""

    def get_fail_safe(self) -> EventTripleOutput:
        return EventTripleOutput(
            subject=self.input_schema.__fields__['persona_name'].default or "persona",
            predicate="is",
            object="idle"
        )


# ============================================================================
# 3. Action Object Description Prompt
# ============================================================================

class ActObjDescPrompt(BasePrompt[ActObjDescInput, ActObjDescOutput]):
    """Describes what state an object is in during an action."""

    input_schema = ActObjDescInput
    output_schema = ActObjDescOutput

    def render_prompt(self, input_data: ActObjDescInput) -> str:
        return f"""Determine the state of the object.

{input_data.game_object} is being used by {input_data.persona_name}.
{input_data.persona_name} is {input_data.action_description}.

What is the state of {input_data.game_object}? (e.g., being fixed, being used, being read)
The {input_data.game_object} is <fill in>"""

    def get_fail_safe(self) -> ActObjDescOutput:
        return ActObjDescOutput(object_state="idle")


# ============================================================================
# 4. Action Object Event Triple Prompt
# ============================================================================

class ActObjEventTriplePrompt(BasePrompt[ActObjEventTripleInput, ActObjEventTripleOutput]):
    """Extracts subject-predicate-object triple for an object's state."""

    input_schema = ActObjEventTripleInput
    output_schema = ActObjEventTripleOutput

    def render_prompt(self, input_data: ActObjEventTripleInput) -> str:
        return f"""Task: Turn the input into (subject, predicate, object). Output ONLY the triple.

Input: bed is being slept on.
Output: (bed, is, being slept on)
---
Input: coffee machine is brewing coffee.
Output: (coffee machine, is, brewing coffee)
---
Input: computer is being used.
Output: (computer, is, being used)
---
Input: {input_data.game_object} is {input_data.object_description}.
Output:"""

    def get_fail_safe(self) -> ActObjEventTripleOutput:
        return ActObjEventTripleOutput(
            subject=self.input_schema.__fields__['game_object'].default or "object",
            predicate="is",
            object="idle"
        )


# ============================================================================
# 5. Event Poignancy Prompt
# ============================================================================

class EventPoignancyPrompt(BasePrompt[EventPoignancyInput, EventPoignancyOutput]):
    """Rates the poignancy/importance of an event for a persona."""

    input_schema = EventPoignancyInput
    output_schema = EventPoignancyOutput

    def render_prompt(self, input_data: EventPoignancyInput) -> str:
        return f"""Here is a brief description of {input_data.persona_name}.
{input_data.identity_stable_set}

On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for {input_data.persona_name}.

Event: {input_data.event_description}
Rate (return a number between 1 to 10):"""

    def get_fail_safe(self) -> EventPoignancyOutput:
        return EventPoignancyOutput(rating=4)


# ============================================================================
# 6. Thought Poignancy Prompt
# ============================================================================

class ThoughtPoignancyPrompt(BasePrompt[ThoughtPoignancyInput, ThoughtPoignancyOutput]):
    """Rates the poignancy/importance of a thought for a persona."""

    input_schema = ThoughtPoignancyInput
    output_schema = ThoughtPoignancyOutput

    def render_prompt(self, input_data: ThoughtPoignancyInput) -> str:
        return f"""Here is a brief description of {input_data.persona_name}.
{input_data.identity_stable_set}

On the scale of 1 to 10, where 1 is purely mundane (e.g., idle daydream) and 10 is extremely poignant (e.g., life-changing realization), rate the likely poignancy of the following thought for {input_data.persona_name}.

Thought: {input_data.thought_description}
Rate (return a number between 1 to 10):"""

    def get_fail_safe(self) -> ThoughtPoignancyOutput:
        return ThoughtPoignancyOutput(rating=4)


# ============================================================================
# 7. Chat Poignancy Prompt
# ============================================================================

class ChatPoignancyPrompt(BasePrompt[ChatPoignancyInput, ChatPoignancyOutput]):
    """Rates the poignancy/importance of a conversation for a persona."""

    input_schema = ChatPoignancyInput
    output_schema = ChatPoignancyOutput

    def render_prompt(self, input_data: ChatPoignancyInput) -> str:
        return f"""Here is a brief description of {input_data.persona_name}.
{input_data.identity_stable_set}

On the scale of 1 to 10, where 1 is purely mundane (e.g., small talk about weather) and 10 is extremely poignant (e.g., confession of feelings, life-changing news), rate the likely poignancy of the following conversation for {input_data.persona_name}.

Conversation: {input_data.chat_description}
Rate (return a number between 1 to 10):"""

    def get_fail_safe(self) -> ChatPoignancyOutput:
        return ChatPoignancyOutput(rating=4)
