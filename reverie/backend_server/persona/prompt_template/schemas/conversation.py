"""
Pydantic schemas for conversation-related prompts.

This module contains input and output models for conversation prompts including:
- Deciding whether to talk or react
- Creating and summarizing conversations
- Agent chat generation
- Next conversation line generation
"""

from typing import List
from pydantic import BaseModel, Field


# ============================================================================
# 1. Decide To Talk Prompt
# ============================================================================

class DecideToTalkInput(BaseModel):
    """Input for deciding whether persona should initiate conversation."""
    context: str = Field(..., description="Recent events and thoughts")
    current_time: str = Field(..., description="Current timestamp")
    persona_name: str = Field(..., description="Persona's name")
    target_name: str = Field(..., description="Target person's name")
    last_chatted_time: str = Field(default="", description="When they last chatted")
    last_chat_about: str = Field(default="", description="What they last talked about")
    persona_activity: str = Field(..., description="What persona is currently doing")
    target_activity: str = Field(..., description="What target is currently doing")


class DecideToTalkOutput(BaseModel):
    """Output for decide to talk decision."""
    should_talk: bool = Field(..., description="Whether to initiate conversation")


# ============================================================================
# 2. Decide To React Prompt
# ============================================================================

class DecideToReactInput(BaseModel):
    """Input for deciding how to react to another persona."""
    context: str = Field(..., description="Recent events and thoughts")
    current_time: str = Field(..., description="Current timestamp")
    persona_activity: str = Field(..., description="What persona is doing")
    target_activity: str = Field(..., description="What target is doing")
    persona_name: str = Field(..., description="Persona's name")
    persona_action: str = Field(..., description="Persona's current action")
    target_name: str = Field(..., description="Target person's name")
    target_action: str = Field(..., description="Target's current action")


class DecideToReactOutput(BaseModel):
    """Output for decide to react decision."""
    option: int = Field(..., ge=1, le=3, description="Reaction option: 1=do nothing, 2=react, 3=wait")


# ============================================================================
# 3. Create Conversation Prompt
# ============================================================================

class ConversationTurn(BaseModel):
    """A single turn in a conversation."""
    speaker: str = Field(..., description="Name of the speaker")
    utterance: str = Field(..., description="What they said")


class CreateConversationInput(BaseModel):
    """Input for creating a full conversation."""
    current_date: str = Field(..., description="Current date")
    location: str = Field(..., description="Where the conversation is taking place")
    previous_conversation_context: str = Field(default="", description="Context from previous conversations")
    persona_name: str = Field(..., description="Persona's name")
    target_name: str = Field(..., description="Target person's name")
    persona_identity: str = Field(..., description="Persona's identity stable set")
    target_identity: str = Field(..., description="Target's identity stable set")


class CreateConversationOutput(BaseModel):
    """Output for created conversation."""
    conversation: List[ConversationTurn] = Field(
        ...,
        description="List of conversation turns"
    )


# ============================================================================
# 4. Summarize Conversation Prompt
# ============================================================================

class SummarizeConversationInput(BaseModel):
    """Input for summarizing a conversation."""
    conversation_text: str = Field(..., description="The full conversation to summarize")


class SummarizeConversationOutput(BaseModel):
    """Output for conversation summary."""
    summary: str = Field(..., description="Summary of the conversation (starting with 'conversing about')")


# ============================================================================
# 5. Agent Chat Prompt (Iterative conversation generation)
# ============================================================================

class AgentChatInput(BaseModel):
    """Input for agent chat generation."""
    persona_currently: str = Field(..., description="What persona is currently doing")
    target_currently: str = Field(..., description="What target is currently doing")
    previous_conversation_context: str = Field(default="", description="Context from previous conversation")
    current_context: str = Field(..., description="Current situational context")
    current_location: str = Field(..., description="Current location")
    persona_name: str = Field(..., description="Persona's name")
    persona_summary_idea: str = Field(..., description="Persona's summarized idea/intent")
    target_name: str = Field(..., description="Target's name")
    target_summary_idea: str = Field(..., description="Target's summarized idea/intent")


class AgentChatOutput(BaseModel):
    """Output for agent chat."""
    conversation: List[ConversationTurn] = Field(
        ...,
        description="Generated conversation"
    )


# ============================================================================
# 6. Agent Chat Summarize Ideas Prompt
# ============================================================================

class AgentChatSummarizeIdeasInput(BaseModel):
    """Input for summarizing ideas from agent chat."""
    statements: str = Field(..., description="Statements to summarize")
    persona_name: str = Field(..., description="Persona's name")
    question: str = Field(..., description="Question to answer from the statements")


class AgentChatSummarizeIdeasOutput(BaseModel):
    """Output for summarized ideas."""
    summary: str = Field(..., description="Summary answering the question")


# ============================================================================
# 7. Agent Chat Summarize Relationship Prompt
# ============================================================================

class AgentChatSummarizeRelationshipInput(BaseModel):
    """Input for summarizing relationship from agent chat."""
    statements: str = Field(..., description="Statements about the relationship")
    persona_name: str = Field(..., description="Persona's name")
    target_name: str = Field(..., description="Target's name")


class AgentChatSummarizeRelationshipOutput(BaseModel):
    """Output for relationship summary."""
    relationship: str = Field(..., description="Description of the relationship")


# ============================================================================
# 8. Generate Next Conversation Line Prompt
# ============================================================================

class GenerateNextConvoLineInput(BaseModel):
    """Input for generating next line in conversation."""
    persona_name: str = Field(..., description="Persona's name")
    persona_identity: str = Field(..., description="Persona's identity stable set")
    interlocutor_desc: str = Field(..., description="Description of who they're talking to")
    previous_conversation: str = Field(..., description="Previous conversation context")
    retrieved_summary: str = Field(..., description="Retrieved relevant memories/thoughts")


class GenerateNextConvoLineOutput(BaseModel):
    """Output for next conversation line."""
    utterance: str = Field(..., description="The next thing the persona says")


# ============================================================================
# 9. Planning Thought On Conversation Prompt
# ============================================================================

class PlanningThoughtOnConvoInput(BaseModel):
    """Input for generating planning thought about a conversation."""
    persona_name: str = Field(..., description="Persona's name")
    conversation_summary: str = Field(..., description="Summary of the conversation")


class PlanningThoughtOnConvoOutput(BaseModel):
    """Output for planning thought."""
    thought: str = Field(..., description="Planning thought about the conversation")


# ============================================================================
# 10. Memo On Conversation Prompt
# ============================================================================

class MemoOnConvoInput(BaseModel):
    """Input for creating a memo about a conversation."""
    persona_name: str = Field(..., description="Persona's name")
    conversation_summary: str = Field(..., description="Summary of the conversation")
    target_name: str = Field(..., description="Who they talked to")


class MemoOnConvoOutput(BaseModel):
    """Output for conversation memo."""
    memo: str = Field(..., description="Memo about the conversation")
