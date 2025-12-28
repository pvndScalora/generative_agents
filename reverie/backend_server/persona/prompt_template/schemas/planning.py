"""
Pydantic schemas for planning-related prompts.

This module contains input and output models for all planning prompts including:
- Wake up hour prediction
- Daily plan generation
- Hourly schedule generation
- Task decomposition
- Action location selection (sector, arena, game object)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# 1. Wake Up Hour Prompt
# ============================================================================

class WakeUpHourInput(BaseModel):
    """Input for predicting wake up hour."""
    identity_stable_set: str = Field(..., description="Persona's core identity and traits")
    lifestyle: str = Field(..., description="Lifestyle description including sleep habits")
    first_name: str = Field(..., description="First name of the persona")


class WakeUpHourOutput(BaseModel):
    """Output for wake up hour prediction."""
    hour: int = Field(..., ge=0, le=23, description="Wake up hour in 24-hour format")


# ============================================================================
# 2. Daily Plan Prompt
# ============================================================================

class DailyPlanInput(BaseModel):
    """Input for generating daily plan."""
    identity_stable_set: str = Field(..., description="Persona's core identity")
    lifestyle: str = Field(..., description="Lifestyle description")
    current_date: str = Field(..., description="Current date string")
    first_name: str = Field(..., description="First name")
    wake_up_hour: str = Field(..., description="Wake up time (e.g., '7:00 am')")


class DailyPlanOutput(BaseModel):
    """Output for daily plan."""
    activities: List[str] = Field(
        ...,
        description="List of planned activities for the day"
    )


# ============================================================================
# 3. Hourly Schedule Prompt
# ============================================================================

class HourlyScheduleInput(BaseModel):
    """Input for generating hourly schedule."""
    schedule_format: str = Field(..., description="Template for schedule format")
    identity_stable_set: str = Field(..., description="Persona's core identity")
    prior_schedule: str = Field(..., description="Previously generated schedule")
    daily_plan_req: str = Field(..., description="Daily requirements/intentions")
    intermission: str = Field(default="", description="Additional context or interruptions")
    prompt_ending: str = Field(..., description="Prompt ending with current time")


class HourlyScheduleOutput(BaseModel):
    """Output for hourly schedule."""
    activity: str = Field(..., description="The activity for the current hour")


# ============================================================================
# 4. Task Decomposition Prompt
# ============================================================================

class SubTask(BaseModel):
    """A subtask with description and duration."""
    description: str = Field(..., description="What the persona is doing")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")


class TaskDecompInput(BaseModel):
    """Input for decomposing a task into subtasks."""
    identity_stable_set: str = Field(..., description="Persona's core identity")
    schedule_summary: str = Field(..., description="Summary of today's schedule context")
    first_name: str = Field(..., description="First name")
    task: str = Field(..., description="The task to decompose")
    time_range: str = Field(..., description="Time range for the task")
    duration_minutes: int = Field(..., description="Total duration in minutes")


class TaskDecompOutput(BaseModel):
    """Output for task decomposition."""
    subtasks: List[SubTask] = Field(
        ...,
        description="List of subtasks with durations"
    )


# ============================================================================
# 5. Action Sector Prompt (Location Selection - Sector Level)
# ============================================================================

class ActionSectorInput(BaseModel):
    """Input for selecting which sector to perform an action in."""
    persona_name: str = Field(..., description="Persona's full name")
    living_area: str = Field(..., description="Persona's living area")
    living_area_arenas: str = Field(..., description="Accessible arenas in living area")
    current_sector: str = Field(..., description="Current sector location")
    current_sector_arenas: str = Field(..., description="Accessible arenas in current sector")
    daily_plan_req: str = Field(default="", description="Daily plan context")
    accessible_sectors: str = Field(..., description="All accessible sectors")
    action_description: str = Field(..., description="The action being performed")
    action_detail: str = Field(..., description="Detail of the action (from parentheses)")


class ActionSectorOutput(BaseModel):
    """Output for action sector selection."""
    sector: str = Field(..., description="The selected sector name")


# ============================================================================
# 6. Action Arena Prompt (Location Selection - Arena Level)
# ============================================================================

class ActionArenaInput(BaseModel):
    """Input for selecting which arena to perform an action in."""
    persona_name: str = Field(..., description="Persona's full name")
    sector: str = Field(..., description="The sector to search within")
    accessible_arenas: str = Field(..., description="Accessible arenas in the sector")
    action_description: str = Field(..., description="The action being performed")
    action_detail: str = Field(..., description="Detail of the action")


class ActionArenaOutput(BaseModel):
    """Output for action arena selection."""
    arena: str = Field(..., description="The selected arena name")


# ============================================================================
# 7. Action Game Object Prompt (Location Selection - Object Level)
# ============================================================================

class ActionGameObjectInput(BaseModel):
    """Input for selecting which game object to interact with."""
    action_description: str = Field(..., description="The action being performed")
    accessible_objects: str = Field(..., description="Accessible objects in the arena")


class ActionGameObjectOutput(BaseModel):
    """Output for game object selection."""
    game_object: str = Field(..., description="The selected game object name")


# ============================================================================
# 8. New Decomp Schedule Prompt (Updating task decomposition)
# ============================================================================

class NewDecompScheduleInput(BaseModel):
    """Input for updating/revising task decomposition schedule."""
    identity_stable_set: str = Field(..., description="Persona's core identity")
    schedule_summary: str = Field(..., description="Current schedule context")
    first_name: str = Field(..., description="First name")
    current_task: str = Field(..., description="Current task being revised")
    remaining_duration: int = Field(..., description="Remaining minutes for the task")


class NewDecompScheduleOutput(BaseModel):
    """Output for revised task decomposition."""
    subtasks: List[SubTask] = Field(
        ...,
        description="Revised list of subtasks"
    )
