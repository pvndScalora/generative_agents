"""
Conversation prompt implementations with f-string templates.

This module contains all conversation-related prompts that help personas:
- Decide whether to initiate conversations
- Generate full conversations
- Summarize conversations
- Generate individual utterances
"""

from typing import List
from persona.prompt_template.core.base import BasePrompt
from persona.prompt_template.schemas.conversation import (
    DecideToTalkInput, DecideToTalkOutput,
    DecideToReactInput, DecideToReactOutput,
    CreateConversationInput, CreateConversationOutput, ConversationTurn,
    SummarizeConversationInput, SummarizeConversationOutput,
    AgentChatInput, AgentChatOutput,
    AgentChatSummarizeIdeasInput, AgentChatSummarizeIdeasOutput,
    AgentChatSummarizeRelationshipInput, AgentChatSummarizeRelationshipOutput,
    GenerateNextConvoLineInput, GenerateNextConvoLineOutput,
    PlanningThoughtOnConvoInput, PlanningThoughtOnConvoOutput,
    MemoOnConvoInput, MemoOnConvoOutput,
)


# ============================================================================
# 1. Decide To Talk Prompt
# ============================================================================

class DecideToTalkPrompt(BasePrompt[DecideToTalkInput, DecideToTalkOutput]):
    """Decides whether the persona should initiate a conversation."""

    input_schema = DecideToTalkInput
    output_schema = DecideToTalkOutput

    def render_prompt(self, input_data: DecideToTalkInput) -> str:
        last_chat_info = ""
        if input_data.last_chatted_time and input_data.last_chat_about:
            last_chat_info = f"{input_data.persona_name} and {input_data.target_name} last chatted at {input_data.last_chatted_time} about: {input_data.last_chat_about}\n"

        return f"""{input_data.context}

Current time: {input_data.current_time}

{last_chat_info}
{input_data.persona_activity}
{input_data.target_activity}

Should {input_data.persona_name} initiate a conversation with {input_data.target_name}?
Answer in yes or no:"""

    def get_fail_safe(self) -> DecideToTalkOutput:
        return DecideToTalkOutput(should_talk=True)


# ============================================================================
# 2. Decide To React Prompt
# ============================================================================

class DecideToReactPrompt(BasePrompt[DecideToReactInput, DecideToReactOutput]):
    """Decides how the persona should react to seeing another persona."""

    input_schema = DecideToReactInput
    output_schema = DecideToReactOutput

    def render_prompt(self, input_data: DecideToReactInput) -> str:
        return f"""{input_data.context}

Current time: {input_data.current_time}

{input_data.persona_activity}
{input_data.target_activity}

How should {input_data.persona_name} react?
Option 1: {input_data.persona_name} should keep {input_data.persona_action}
Option 2: {input_data.persona_name} should react and try to start a conversation
Option 3: {input_data.persona_name} should wait and see what {input_data.target_name} does

Answer: Option"""

    def get_fail_safe(self) -> DecideToReactOutput:
        return DecideToReactOutput(option=3)


# ============================================================================
# 3. Create Conversation Prompt
# ============================================================================

class CreateConversationPrompt(BasePrompt[CreateConversationInput, CreateConversationOutput]):
    """Creates a full conversation between two personas."""

    input_schema = CreateConversationInput
    output_schema = CreateConversationOutput

    def render_prompt(self, input_data: CreateConversationInput) -> str:
        prev_context = ""
        if input_data.previous_conversation_context:
            prev_context = f"\n{input_data.previous_conversation_context}\n"

        return f"""It is {input_data.current_date}. {input_data.persona_name} and {input_data.target_name} are at {input_data.location}.{prev_context}

Here is some background about {input_data.persona_name}:
{input_data.persona_identity}

Here is some background about {input_data.target_name}:
{input_data.target_identity}

Here is their conversation.
{input_data.persona_name}:"""

    def get_fail_safe(self) -> CreateConversationOutput:
        return CreateConversationOutput(conversation=[
            ConversationTurn(speaker="Person", utterance="...")
        ])


# ============================================================================
# 4. Summarize Conversation Prompt
# ============================================================================

class SummarizeConversationPrompt(BasePrompt[SummarizeConversationInput, SummarizeConversationOutput]):
    """Summarizes a conversation."""

    input_schema = SummarizeConversationInput
    output_schema = SummarizeConversationOutput

    def render_prompt(self, input_data: SummarizeConversationInput) -> str:
        return f"""Summarize the following conversation.

{input_data.conversation_text}

The summary should be: conversing about"""

    def get_fail_safe(self) -> SummarizeConversationOutput:
        return SummarizeConversationOutput(summary="conversing about daily activities")


# ============================================================================
# 5. Agent Chat Prompt
# ============================================================================

class AgentChatPrompt(BasePrompt[AgentChatInput, AgentChatOutput]):
    """Generates an iterative conversation between two agents."""

    input_schema = AgentChatInput
    output_schema = AgentChatOutput

    def render_prompt(self, input_data: AgentChatInput) -> str:
        prev_context = ""
        if input_data.previous_conversation_context:
            prev_context = f"\n{input_data.previous_conversation_context}\n"

        return f"""{input_data.persona_name} is {input_data.persona_currently}
{input_data.target_name} is {input_data.target_currently}{prev_context}

{input_data.current_context}

They are at {input_data.current_location}.

{input_data.persona_name} wants to {input_data.persona_summary_idea}
Meanwhile, {input_data.target_name} wants to {input_data.target_summary_idea}

Here is their conversation.
{input_data.persona_name}:"""

    def get_fail_safe(self) -> AgentChatOutput:
        return AgentChatOutput(conversation=[
            ConversationTurn(speaker="Person", utterance="...")
        ])


# ============================================================================
# 6. Agent Chat Summarize Ideas Prompt
# ============================================================================

class AgentChatSummarizeIdeasPrompt(BasePrompt[AgentChatSummarizeIdeasInput, AgentChatSummarizeIdeasOutput]):
    """Summarizes ideas from statements for agent chat."""

    input_schema = AgentChatSummarizeIdeasInput
    output_schema = AgentChatSummarizeIdeasOutput

    def render_prompt(self, input_data: AgentChatSummarizeIdeasInput) -> str:
        return f"""{input_data.statements}

Given the above statements, what does {input_data.persona_name} want to say about {input_data.question}?"""

    def get_fail_safe(self) -> AgentChatSummarizeIdeasOutput:
        return AgentChatSummarizeIdeasOutput(summary="...")


# ============================================================================
# 7. Agent Chat Summarize Relationship Prompt
# ============================================================================

class AgentChatSummarizeRelationshipPrompt(BasePrompt[AgentChatSummarizeRelationshipInput, AgentChatSummarizeRelationshipOutput]):
    """Summarizes the relationship between two personas."""

    input_schema = AgentChatSummarizeRelationshipInput
    output_schema = AgentChatSummarizeRelationshipOutput

    def render_prompt(self, input_data: AgentChatSummarizeRelationshipInput) -> str:
        return f"""{input_data.statements}

How does {input_data.persona_name} feel about {input_data.target_name}?"""

    def get_fail_safe(self) -> AgentChatSummarizeRelationshipOutput:
        return AgentChatSummarizeRelationshipOutput(relationship="neutral acquaintance")


# ============================================================================
# 8. Generate Next Conversation Line Prompt
# ============================================================================

class GenerateNextConvoLinePrompt(BasePrompt[GenerateNextConvoLineInput, GenerateNextConvoLineOutput]):
    """Generates the next line in an ongoing conversation."""

    input_schema = GenerateNextConvoLineInput
    output_schema = GenerateNextConvoLineOutput

    def render_prompt(self, input_data: GenerateNextConvoLineInput) -> str:
        return f"""{input_data.persona_name}'s background:
{input_data.persona_identity}

{input_data.persona_name} is talking to {input_data.interlocutor_desc}

Previous conversation:
{input_data.previous_conversation}

Relevant memories:
{input_data.retrieved_summary}

What does {input_data.persona_name} say next?
{input_data.persona_name}:"""

    def get_fail_safe(self) -> GenerateNextConvoLineOutput:
        return GenerateNextConvoLineOutput(utterance="...")


# ============================================================================
# 9. Planning Thought On Conversation Prompt
# ============================================================================

class PlanningThoughtOnConvoPrompt(BasePrompt[PlanningThoughtOnConvoInput, PlanningThoughtOnConvoOutput]):
    """Generates a planning thought based on a conversation."""

    input_schema = PlanningThoughtOnConvoInput
    output_schema = PlanningThoughtOnConvoOutput

    def render_prompt(self, input_data: PlanningThoughtOnConvoInput) -> str:
        return f"""{input_data.persona_name} just had a conversation: {input_data.conversation_summary}

What is {input_data.persona_name} thinking about in terms of planning?
{input_data.persona_name} is thinking:"""

    def get_fail_safe(self) -> PlanningThoughtOnConvoOutput:
        return PlanningThoughtOnConvoOutput(thought="continuing with the current plan")


# ============================================================================
# 10. Memo On Conversation Prompt
# ============================================================================

class MemoOnConvoPrompt(BasePrompt[MemoOnConvoInput, MemoOnConvoOutput]):
    """Creates a memo/note about a conversation."""

    input_schema = MemoOnConvoInput
    output_schema = MemoOnConvoOutput

    def render_prompt(self, input_data: MemoOnConvoInput) -> str:
        return f"""{input_data.persona_name} had a conversation with {input_data.target_name}: {input_data.conversation_summary}

Create a brief memo about this conversation for {input_data.persona_name}:"""

    def get_fail_safe(self) -> MemoOnConvoOutput:
        return MemoOnConvoOutput(memo="Had a conversation")
