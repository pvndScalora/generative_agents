"""
Pydantic schemas for reflection-related prompts.

This module contains input and output models for reflection prompts including:
- Keyword extraction from descriptions
- Generating thoughts from keywords
- Converting conversations to thoughts
- Focal point generation
- Insight and guidance extraction
- Inner thought generation
"""

from typing import List, Dict, Set
from pydantic import BaseModel, Field


# ============================================================================
# 1. Extract Keywords Prompt
# ============================================================================

class ExtractKeywordsInput(BaseModel):
    """Input for extracting keywords from a description."""
    description: str = Field(..., description="Description to extract keywords from")


class ExtractKeywordsOutput(BaseModel):
    """Output for keyword extraction."""
    keywords: Set[str] = Field(..., description="Set of extracted keywords (factual and emotive)")


# ============================================================================
# 2. Keyword To Thoughts Prompt
# ============================================================================

class KeywordToThoughtsInput(BaseModel):
    """Input for generating thoughts from a keyword."""
    keyword: str = Field(..., description="The keyword to expand on")
    concept_summary: str = Field(..., description="Summary of related concepts")
    persona_name: str = Field(..., description="Persona's name")


class KeywordToThoughtsOutput(BaseModel):
    """Output for keyword-based thought generation."""
    thought: str = Field(..., description="Generated thought from the keyword")


# ============================================================================
# 3. Conversation To Thoughts Prompt
# ============================================================================

class ConvoToThoughtsInput(BaseModel):
    """Input for converting a conversation to thoughts."""
    init_persona_name: str = Field(..., description="Initiating persona's name")
    target_persona_name: str = Field(..., description="Target persona's name")
    conversation_text: str = Field(..., description="The conversation text")
    target_for_thought: str = Field(..., description="Who the thought is about")


class ConvoToThoughtsOutput(BaseModel):
    """Output for conversation-to-thought conversion."""
    thought: str = Field(..., description="Thought derived from the conversation")


# ============================================================================
# 4. Focal Point Prompt
# ============================================================================

class FocalPtInput(BaseModel):
    """Input for generating focal points/questions."""
    statements: str = Field(..., description="Statements to generate questions from")
    num_questions: int = Field(..., ge=1, le=20, description="Number of questions to generate")


class FocalPtOutput(BaseModel):
    """Output for focal points."""
    questions: List[str] = Field(..., description="List of focal point questions")


# ============================================================================
# 5. Insight And Guidance Prompt
# ============================================================================

class InsightAndGuidanceInput(BaseModel):
    """Input for extracting insights and evidence."""
    statements: str = Field(..., description="Statements to extract insights from")
    num_insights: int = Field(..., ge=1, le=20, description="Number of insights to generate")


class InsightAndGuidanceOutput(BaseModel):
    """Output for insights with evidence."""
    insights: Dict[str, List[int]] = Field(
        ...,
        description="Map of insight to evidence statement indices"
    )


# ============================================================================
# 6. Summarize Ideas Prompt
# ============================================================================

class SummarizeIdeasInput(BaseModel):
    """Input for summarizing ideas."""
    statements: str = Field(..., description="Statements to summarize")
    persona_name: str = Field(..., description="Persona's name")
    question: str = Field(..., description="Question to answer from statements")


class SummarizeIdeasOutput(BaseModel):
    """Output for summarized ideas."""
    summary: str = Field(..., description="Summary answering the question")


# ============================================================================
# 7. Whisper Inner Thought Prompt
# ============================================================================

class WhisperInnerThoughtInput(BaseModel):
    """Input for generating inner thought from a whisper/utterance."""
    persona_name: str = Field(..., description="Persona's name")
    whisper: str = Field(..., description="The utterance/whisper to reflect on")


class WhisperInnerThoughtOutput(BaseModel):
    """Output for inner thought."""
    inner_thought: str = Field(..., description="The persona's inner thought")
