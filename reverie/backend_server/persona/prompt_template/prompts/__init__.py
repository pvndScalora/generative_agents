"""
Prompt implementations with f-string templates.
"""

# Core base class
from persona.prompt_template.core.base import BasePrompt

# Planning prompts
from .planning import (
    WakeUpHourPrompt,
    DailyPlanPrompt,
    HourlySchedulePrompt,
    TaskDecompPrompt,
    ActionSectorPrompt,
    ActionArenaPrompt,
    ActionGameObjectPrompt,
    NewDecompSchedulePrompt,
)

# Perception prompts
from .perception import (
    PronunciatioPrompt,
    EventTriplePrompt,
    ActObjDescPrompt,
    ActObjEventTriplePrompt,
    EventPoignancyPrompt,
    ThoughtPoignancyPrompt,
    ChatPoignancyPrompt,
)

# Conversation prompts
from .conversation import (
    DecideToTalkPrompt,
    DecideToReactPrompt,
    CreateConversationPrompt,
    SummarizeConversationPrompt,
    AgentChatPrompt,
    AgentChatSummarizeIdeasPrompt,
    AgentChatSummarizeRelationshipPrompt,
    GenerateNextConvoLinePrompt,
    PlanningThoughtOnConvoPrompt,
    MemoOnConvoPrompt,
)

# Reflection prompts
from .reflection import (
    ExtractKeywordsPrompt,
    KeywordToThoughtsPrompt,
    ConvoToThoughtsPrompt,
    FocalPtPrompt,
    InsightAndGuidancePrompt,
    SummarizeIdeasPrompt,
    WhisperInnerThoughtPrompt,
)

# Planning schemas (for input construction)
from persona.prompt_template.schemas.planning import (
    WakeUpHourInput,
    DailyPlanInput,
    HourlyScheduleInput,
    TaskDecompInput,
    ActionSectorInput,
    ActionArenaInput,
    ActionGameObjectInput,
    NewDecompScheduleInput,
)

# Perception schemas
from persona.prompt_template.schemas.perception import (
    PronunciatioInput,
    EventTripleInput,
    ActObjDescInput,
    ActObjEventTripleInput,
    EventPoignancyInput,
    ThoughtPoignancyInput,
    ChatPoignancyInput,
)

# Conversation schemas
from persona.prompt_template.schemas.conversation import (
    DecideToTalkInput,
    DecideToReactInput,
    CreateConversationInput,
    SummarizeConversationInput,
    AgentChatInput,
    AgentChatSummarizeIdeasInput,
    AgentChatSummarizeRelationshipInput,
    GenerateNextConvoLineInput,
    PlanningThoughtOnConvoInput,
    MemoOnConvoInput,
)

# Reflection schemas
from persona.prompt_template.schemas.reflection import (
    ExtractKeywordsInput,
    KeywordToThoughtsInput,
    ConvoToThoughtsInput,
    FocalPtInput,
    InsightAndGuidanceInput,
    SummarizeIdeasInput,
    WhisperInnerThoughtInput,
)

__all__ = [
    # Core
    "BasePrompt",
    # Planning
    "WakeUpHourPrompt",
    "DailyPlanPrompt",
    "HourlySchedulePrompt",
    "TaskDecompPrompt",
    "ActionSectorPrompt",
    "ActionArenaPrompt",
    "ActionGameObjectPrompt",
    "NewDecompSchedulePrompt",
    # Perception
    "PronunciatioPrompt",
    "EventTriplePrompt",
    "ActObjDescPrompt",
    "ActObjEventTriplePrompt",
    "EventPoignancyPrompt",
    "ThoughtPoignancyPrompt",
    "ChatPoignancyPrompt",
    # Conversation
    "DecideToTalkPrompt",
    "DecideToReactPrompt",
    "CreateConversationPrompt",
    "SummarizeConversationPrompt",
    "AgentChatPrompt",
    "AgentChatSummarizeIdeasPrompt",
    "AgentChatSummarizeRelationshipPrompt",
    "GenerateNextConvoLinePrompt",
    "PlanningThoughtOnConvoPrompt",
    "MemoOnConvoPrompt",
    # Reflection
    "ExtractKeywordsPrompt",
    "KeywordToThoughtsPrompt",
    "ConvoToThoughtsPrompt",
    "FocalPtPrompt",
    "InsightAndGuidancePrompt",
    "SummarizeIdeasPrompt",
    "WhisperInnerThoughtPrompt",
    # Input schemas
    "WakeUpHourInput",
    "DailyPlanInput",
    "HourlyScheduleInput",
    "TaskDecompInput",
    "ActionSectorInput",
    "ActionArenaInput",
    "ActionGameObjectInput",
    "NewDecompScheduleInput",
    "PronunciatioInput",
    "EventTripleInput",
    "ActObjDescInput",
    "ActObjEventTripleInput",
    "EventPoignancyInput",
    "ThoughtPoignancyInput",
    "ChatPoignancyInput",
    "DecideToTalkInput",
    "DecideToReactInput",
    "CreateConversationInput",
    "SummarizeConversationInput",
    "AgentChatInput",
    "AgentChatSummarizeIdeasInput",
    "AgentChatSummarizeRelationshipInput",
    "GenerateNextConvoLineInput",
    "PlanningThoughtOnConvoInput",
    "MemoOnConvoInput",
    "ExtractKeywordsInput",
    "KeywordToThoughtsInput",
    "ConvoToThoughtsInput",
    "FocalPtInput",
    "InsightAndGuidanceInput",
    "SummarizeIdeasInput",
    "WhisperInnerThoughtInput",
]
