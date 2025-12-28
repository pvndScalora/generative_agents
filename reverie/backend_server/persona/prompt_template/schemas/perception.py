"""
Pydantic schemas for perception-related prompts.

This module contains input and output models for perception prompts including:
- Emoji/pronunciatio generation
- Event triple extraction
- Action/object description
- Poignancy rating (importance scoring)
"""

from typing import Tuple
from pydantic import BaseModel, Field


# ============================================================================
# 1. Pronunciatio Prompt (Emoji generation for actions)
# ============================================================================

class PronunciatioInput(BaseModel):
    """Input for generating emoji/pronunciatio for an action."""
    action_description: str = Field(..., description="Description of the action")


class PronunciatioOutput(BaseModel):
    """Output for pronunciatio (emoji)."""
    emoji: str = Field(..., max_length=3, description="Emoji representing the action")


# ============================================================================
# 2. Event Triple Prompt (Subject-Predicate-Object extraction)
# ============================================================================

class EventTripleInput(BaseModel):
    """Input for extracting subject-predicate-object triple from event."""
    persona_name: str = Field(..., description="Name of the persona")
    action_description: str = Field(..., description="Description of the action/event")


class EventTripleOutput(BaseModel):
    """Output for event triple extraction."""
    subject: str = Field(..., description="Subject of the event")
    predicate: str = Field(..., description="Predicate/verb of the event")
    object: str = Field(..., description="Object of the event")


# ============================================================================
# 3. Action Object Description Prompt
# ============================================================================

class ActObjDescInput(BaseModel):
    """Input for describing what an object is doing during an action."""
    game_object: str = Field(..., description="The game object name")
    persona_name: str = Field(..., description="Persona's name")
    action_description: str = Field(..., description="What the persona is doing")


class ActObjDescOutput(BaseModel):
    """Output for object description."""
    object_state: str = Field(..., description="What state the object is in")


# ============================================================================
# 4. Action Object Event Triple Prompt
# ============================================================================

class ActObjEventTripleInput(BaseModel):
    """Input for extracting event triple for an object."""
    game_object: str = Field(..., description="The game object name")
    object_description: str = Field(..., description="Description of what the object is doing")


class ActObjEventTripleOutput(BaseModel):
    """Output for object event triple."""
    subject: str = Field(..., description="Subject (the object)")
    predicate: str = Field(..., description="Predicate/verb")
    object: str = Field(..., description="Object complement")


# ============================================================================
# 5. Event Poignancy Prompt (Importance rating for events)
# ============================================================================

class EventPoignancyInput(BaseModel):
    """Input for rating the poignancy/importance of an event."""
    persona_name: str = Field(..., description="Persona's name")
    identity_stable_set: str = Field(..., description="Persona's core identity")
    event_description: str = Field(..., description="Description of the event to rate")


class EventPoignancyOutput(BaseModel):
    """Output for event poignancy rating."""
    rating: int = Field(..., ge=1, le=10, description="Poignancy rating from 1 (mundane) to 10 (extremely important)")


# ============================================================================
# 6. Thought Poignancy Prompt (Importance rating for thoughts)
# ============================================================================

class ThoughtPoignancyInput(BaseModel):
    """Input for rating the poignancy/importance of a thought."""
    persona_name: str = Field(..., description="Persona's name")
    identity_stable_set: str = Field(..., description="Persona's core identity")
    thought_description: str = Field(..., description="Description of the thought to rate")


class ThoughtPoignancyOutput(BaseModel):
    """Output for thought poignancy rating."""
    rating: int = Field(..., ge=1, le=10, description="Poignancy rating from 1 (mundane) to 10 (extremely important)")


# ============================================================================
# 7. Chat Poignancy Prompt (Importance rating for conversations)
# ============================================================================

class ChatPoignancyInput(BaseModel):
    """Input for rating the poignancy/importance of a chat/conversation."""
    persona_name: str = Field(..., description="Persona's name")
    identity_stable_set: str = Field(..., description="Persona's core identity")
    chat_description: str = Field(..., description="Description of the conversation to rate")


class ChatPoignancyOutput(BaseModel):
    """Output for chat poignancy rating."""
    rating: int = Field(..., ge=1, le=10, description="Poignancy rating from 1 (mundane) to 10 (extremely important)")
