"""
Reflection prompt implementations with f-string templates.

This module contains all reflection-related prompts that help personas:
- Extract keywords from experiences
- Generate thoughts from keywords
- Convert conversations to thoughts
- Generate focal points for reflection
- Extract insights from memories
"""

from typing import List, Dict, Set
from persona.prompt_template.core.base import BasePrompt
from persona.prompt_template.schemas.reflection import (
    ExtractKeywordsInput, ExtractKeywordsOutput,
    KeywordToThoughtsInput, KeywordToThoughtsOutput,
    ConvoToThoughtsInput, ConvoToThoughtsOutput,
    FocalPtInput, FocalPtOutput,
    InsightAndGuidanceInput, InsightAndGuidanceOutput,
    SummarizeIdeasInput, SummarizeIdeasOutput,
    WhisperInnerThoughtInput, WhisperInnerThoughtOutput,
)


# ============================================================================
# 1. Extract Keywords Prompt
# ============================================================================

class ExtractKeywordsPrompt(BasePrompt[ExtractKeywordsInput, ExtractKeywordsOutput]):
    """Extracts factual and emotive keywords from a description."""

    input_schema = ExtractKeywordsInput
    output_schema = ExtractKeywordsOutput

    def render_prompt(self, input_data: ExtractKeywordsInput) -> str:
        # Replace line breaks for better formatting
        description = input_data.description.replace("\n", " <LINE_BREAK> ")

        return f"""Extract the most important keywords from the following description.
Separate factual keywords from emotive keywords.

Description: {description}

Factual keywords:
Emotive keywords:"""

    def get_fail_safe(self) -> ExtractKeywordsOutput:
        return ExtractKeywordsOutput(keywords=set())


# ============================================================================
# 2. Keyword To Thoughts Prompt
# ============================================================================

class KeywordToThoughtsPrompt(BasePrompt[KeywordToThoughtsInput, KeywordToThoughtsOutput]):
    """Generates thoughts based on a keyword and related concepts."""

    input_schema = KeywordToThoughtsInput
    output_schema = KeywordToThoughtsOutput

    def render_prompt(self, input_data: KeywordToThoughtsInput) -> str:
        return f"""Keyword: {input_data.keyword}

Context: {input_data.concept_summary}

Based on the keyword and context, what is {input_data.persona_name} thinking?
{input_data.persona_name} is thinking:"""

    def get_fail_safe(self) -> KeywordToThoughtsOutput:
        return KeywordToThoughtsOutput(thought="")


# ============================================================================
# 3. Conversation To Thoughts Prompt
# ============================================================================

class ConvoToThoughtsPrompt(BasePrompt[ConvoToThoughtsInput, ConvoToThoughtsOutput]):
    """Converts a conversation into thoughts about what was discussed."""

    input_schema = ConvoToThoughtsInput
    output_schema = ConvoToThoughtsOutput

    def render_prompt(self, input_data: ConvoToThoughtsInput) -> str:
        return f"""{input_data.init_persona_name} and {input_data.target_persona_name} had the following conversation:

{input_data.conversation_text}

What does {input_data.init_persona_name} think about {input_data.target_for_thought} after this conversation?
Thought:"""

    def get_fail_safe(self) -> ConvoToThoughtsOutput:
        return ConvoToThoughtsOutput(thought="")


# ============================================================================
# 4. Focal Point Prompt
# ============================================================================

class FocalPtPrompt(BasePrompt[FocalPtInput, FocalPtOutput]):
    """Generates focal point questions for reflection."""

    input_schema = FocalPtInput
    output_schema = FocalPtOutput

    def render_prompt(self, input_data: FocalPtInput) -> str:
        return f"""Given the following statements:

{input_data.statements}

Generate {input_data.num_questions} high-level questions that would help guide reflection and planning.
The questions should be about the persona's goals, relationships, or important decisions.

Questions (as a JSON list of strings):"""

    def get_fail_safe(self) -> FocalPtOutput:
        return FocalPtOutput(questions=["What should I focus on?"] * max(1, input_data.num_questions or 3))


# ============================================================================
# 5. Insight And Guidance Prompt
# ============================================================================

class InsightAndGuidancePrompt(BasePrompt[InsightAndGuidanceInput, InsightAndGuidanceOutput]):
    """Extracts high-level insights from statements with evidence."""

    input_schema = InsightAndGuidanceInput
    output_schema = InsightAndGuidanceOutput

    def render_prompt(self, input_data: InsightAndGuidanceInput) -> str:
        return f"""Given the following statements (numbered):

{input_data.statements}

Generate {input_data.num_insights} high-level insights based on these statements.
For each insight, cite which statement numbers (e.g., 1, 3, 5) provide evidence.

Format each insight as:
<Insight text> (because of statement numbers: <numbers>)

Insights:"""

    def get_fail_safe(self) -> InsightAndGuidanceOutput:
        return InsightAndGuidanceOutput(insights={"I am learning and growing": [1]} if input_data.num_insights > 0 else {})


# ============================================================================
# 6. Summarize Ideas Prompt
# ============================================================================

class SummarizeIdeasPrompt(BasePrompt[SummarizeIdeasInput, SummarizeIdeasOutput]):
    """Summarizes ideas from statements to answer a specific question."""

    input_schema = SummarizeIdeasInput
    output_schema = SummarizeIdeasOutput

    def render_prompt(self, input_data: SummarizeIdeasInput) -> str:
        return f"""{input_data.statements}

Question: {input_data.question}

Based on the above information, what can we say about {input_data.persona_name} regarding this question?
Summary:"""

    def get_fail_safe(self) -> SummarizeIdeasOutput:
        return SummarizeIdeasOutput(summary="...")


# ============================================================================
# 7. Whisper Inner Thought Prompt
# ============================================================================

class WhisperInnerThoughtPrompt(BasePrompt[WhisperInnerThoughtInput, WhisperInnerThoughtOutput]):
    """Generates an inner thought based on what was whispered/said."""

    input_schema = WhisperInnerThoughtInput
    output_schema = WhisperInnerThoughtOutput

    def render_prompt(self, input_data: WhisperInnerThoughtInput) -> str:
        return f"""{input_data.persona_name} whispered: "{input_data.whisper}"

What is {input_data.persona_name} thinking internally?
Inner thought:"""

    def get_fail_safe(self) -> WhisperInnerThoughtOutput:
        return WhisperInnerThoughtOutput(inner_thought="...")
