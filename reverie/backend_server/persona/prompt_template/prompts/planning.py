"""
Planning prompt implementations with f-string templates.

This module contains all planning-related prompts that determine:
- Daily schedules and wake/sleep times
- Hourly activities
- Task decomposition
- Location selection (sector, arena, object)
"""

from typing import List
from persona.prompt_template.core.base import BasePrompt
from persona.prompt_template.schemas.planning import (
    WakeUpHourInput, WakeUpHourOutput,
    DailyPlanInput, DailyPlanOutput,
    HourlyScheduleInput, HourlyScheduleOutput,
    TaskDecompInput, TaskDecompOutput, SubTask,
    ActionSectorInput, ActionSectorOutput,
    ActionArenaInput, ActionArenaOutput,
    ActionGameObjectInput, ActionGameObjectOutput,
    NewDecompScheduleInput, NewDecompScheduleOutput,
)


# ============================================================================
# 1. Wake Up Hour Prompt
# ============================================================================

class WakeUpHourPrompt(BasePrompt[WakeUpHourInput, WakeUpHourOutput]):
    """Determines what hour a persona wakes up."""

    input_schema = WakeUpHourInput
    output_schema = WakeUpHourOutput

    def render_prompt(self, input_data: WakeUpHourInput) -> str:
        return f"""{input_data.identity_stable_set}

In general, {input_data.lifestyle}

{input_data.first_name}'s wake up hour:"""

    def get_fail_safe(self) -> WakeUpHourOutput:
        return WakeUpHourOutput(hour=8)


# ============================================================================
# 2. Daily Plan Prompt
# ============================================================================

class DailyPlanPrompt(BasePrompt[DailyPlanInput, DailyPlanOutput]):
    """Generates a persona's daily plan."""

    input_schema = DailyPlanInput
    output_schema = DailyPlanOutput

    def render_prompt(self, input_data: DailyPlanInput) -> str:
        return f"""{input_data.identity_stable_set}

In general, {input_data.lifestyle}

Today is {input_data.current_date}. Here is {input_data.first_name}'s plan today in broad-strokes (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm): 1) wake up and complete the morning routine at {input_data.wake_up_hour}, 2)"""

    def get_fail_safe(self) -> DailyPlanOutput:
        return DailyPlanOutput(activities=[
            'wake up and complete the morning routine at 6:00 am',
            'eat breakfast at 7:00 am',
            'read a book from 8:00 am to 12:00 pm',
            'have lunch at 12:00 pm',
            'take a nap from 1:00 pm to 4:00 pm',
            'relax and watch TV from 7:00 pm to 8:00 pm',
            'go to bed at 11:00 pm'
        ])


# ============================================================================
# 3. Hourly Schedule Prompt
# ============================================================================

class HourlySchedulePrompt(BasePrompt[HourlyScheduleInput, HourlyScheduleOutput]):
    """Generates what the persona does in a specific hour."""

    input_schema = HourlyScheduleInput
    output_schema = HourlyScheduleOutput

    def render_prompt(self, input_data: HourlyScheduleInput) -> str:
        prompt = f"{input_data.schedule_format}\n\n{input_data.identity_stable_set}\n\n"
        prompt += f"{input_data.prior_schedule}\n"
        prompt += f"{input_data.daily_plan_req}"

        if input_data.intermission:
            prompt += f"\n{input_data.intermission}"

        prompt += f"\n{input_data.prompt_ending}"
        return prompt

    def get_fail_safe(self) -> HourlyScheduleOutput:
        return HourlyScheduleOutput(activity="asleep")


# ============================================================================
# 4. Task Decomposition Prompt
# ============================================================================

class TaskDecompPrompt(BasePrompt[TaskDecompInput, TaskDecompOutput]):
    """Decomposes a task into 5-minute subtasks."""

    input_schema = TaskDecompInput
    output_schema = TaskDecompOutput

    def render_prompt(self, input_data: TaskDecompInput) -> str:
        # Include example from Kelly Bronson
        example = """Describe subtasks in 5 min increments.
---
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: {kitchen, bedroom, dining, porch, office, bathroom, living room, hallway}.
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.

Today is Saturday May 10. From 08:00am ~09:00am, Kelly is planning on having breakfast, from 09:00am ~ 12:00pm, Kelly is planning on working on the next day's kindergarten lesson plan, and from 12:00 ~ 13pm, Kelly is planning on taking a break.
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Kelly is reviewing the kindergarten curriculum standards. (duration in minutes: 15, minutes left: 165)
2) Kelly is brainstorming ideas for the lesson. (duration in minutes: 30, minutes left: 135)
3) Kelly is creating the lesson plan. (duration in minutes: 30, minutes left: 105)
4) Kelly is creating materials for the lesson. (duration in minutes: 30, minutes left: 75)
5) Kelly is taking a break. (duration in minutes: 15, minutes left: 60)
6) Kelly is reviewing the lesson plan. (duration in minutes: 30, minutes left: 30)
7) Kelly is making final changes to the lesson plan. (duration in minutes: 15, minutes left: 15)
8) Kelly is printing the lesson plan. (duration in minutes: 10, minutes left: 5)
9) Kelly is putting the lesson plan in her bag. (duration in minutes: 5, minutes left: 0)
---
"""
        return f"""{example}
{input_data.identity_stable_set}
{input_data.schedule_summary}
In 5 min increments, list the subtasks {input_data.first_name} does when {input_data.first_name} is {input_data.task} from {input_data.time_range} (total duration in minutes: {input_data.duration_minutes}):
1) {input_data.first_name} is"""

    def get_fail_safe(self) -> TaskDecompOutput:
        return TaskDecompOutput(subtasks=[SubTask(description="asleep", duration_minutes=5)])


# ============================================================================
# 5. Action Sector Prompt (Location - Sector Level)
# ============================================================================

class ActionSectorPrompt(BasePrompt[ActionSectorInput, ActionSectorOutput]):
    """Selects which sector the persona should go to for an action."""

    input_schema = ActionSectorInput
    output_schema = ActionSectorOutput

    def render_prompt(self, input_data: ActionSectorInput) -> str:
        prompt = f"{input_data.persona_name} lives in {input_data.living_area}. "
        prompt += f"{input_data.persona_name} knows of the following areas: {input_data.living_area_arenas}.\n"
        prompt += f"{input_data.persona_name} is currently in {input_data.current_sector}. "
        prompt += f"{input_data.persona_name} knows of the following areas in {input_data.current_sector}: {input_data.current_sector_arenas}.\n"

        if input_data.daily_plan_req:
            prompt += input_data.daily_plan_req

        prompt += f"\n{input_data.persona_name} is planning to {input_data.action_description}. "
        prompt += f"For this, {input_data.persona_name} could go to one of the following areas: {input_data.accessible_sectors}. "
        prompt += f"Where should {input_data.persona_name} go?\n\n"
        prompt += f"Respond with ONLY the exact name of ONE sector from the list above, without any additional words, phrases, or descriptions."

        return prompt

    def get_fail_safe(self) -> ActionSectorOutput:
        return ActionSectorOutput(sector="kitchen")


# ============================================================================
# 6. Action Arena Prompt (Location - Arena Level)
# ============================================================================

class ActionArenaPrompt(BasePrompt[ActionArenaInput, ActionArenaOutput]):
    """Selects which arena within a sector the persona should go to."""

    input_schema = ActionArenaInput
    output_schema = ActionArenaOutput

    def render_prompt(self, input_data: ActionArenaInput) -> str:
        prompt = f"{input_data.persona_name} is in {input_data.sector}. "
        prompt += f"{input_data.persona_name} knows of the following areas in {input_data.sector}: {input_data.accessible_arenas}. "
        prompt += f"{input_data.persona_name} is planning to {input_data.action_description}. "
        prompt += f"Which area in {input_data.sector} should {input_data.persona_name} go to?\n\n"
        prompt += f"Respond with ONLY the exact name of ONE area from the list above, without any additional words, phrases, or descriptions."

        return prompt

    def get_fail_safe(self) -> ActionArenaOutput:
        return ActionArenaOutput(arena="kitchen")


# ============================================================================
# 7. Action Game Object Prompt (Location - Object Level)
# ============================================================================

class ActionGameObjectPrompt(BasePrompt[ActionGameObjectInput, ActionGameObjectOutput]):
    """Selects which object the persona should interact with."""

    input_schema = ActionGameObjectInput
    output_schema = ActionGameObjectOutput

    def render_prompt(self, input_data: ActionGameObjectInput) -> str:
        return f"""To {input_data.action_description}, which object should be used? Choose from the following: {input_data.accessible_objects}."""

    def get_fail_safe(self) -> ActionGameObjectOutput:
        return ActionGameObjectOutput(game_object="bed")


# ============================================================================
# 8. New Decomp Schedule Prompt (Revising task decomposition)
# ============================================================================

class NewDecompSchedulePrompt(BasePrompt[NewDecompScheduleInput, NewDecompScheduleOutput]):
    """Revises task decomposition when plans change."""

    input_schema = NewDecompScheduleInput
    output_schema = NewDecompScheduleOutput

    def render_prompt(self, input_data: NewDecompScheduleInput) -> str:
        return f"""{input_data.identity_stable_set}
{input_data.schedule_summary}

{input_data.first_name} is currently {input_data.current_task} with {input_data.remaining_duration} minutes remaining.
In 5 min increments, list the revised subtasks {input_data.first_name} does:
1) {input_data.first_name} is"""

    def get_fail_safe(self) -> NewDecompScheduleOutput:
        return NewDecompScheduleOutput(subtasks=[SubTask(description="asleep", duration_minutes=5)])
