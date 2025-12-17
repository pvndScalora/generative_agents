"""
Pure functions operating on PersonaState.

These functions contain NO side effects, NO I/O, and NO external dependencies.
They are easily testable and can be used independently of Scratch.

This module follows the Hexagonal Architecture principle of keeping
domain logic pure and separated from infrastructure concerns.
"""
import datetime
from typing import List, Tuple, Optional
from .state import PersonaState


def is_action_finished(state: PersonaState) -> bool:
    """
    Check if the current action has completed.
    
    Args:
        state: The persona's current state.
        
    Returns:
        True if action is finished or no action is set, False otherwise.
    """
    action = state.action_state.current_action
    
    if not action.address:
        return True
    
    # Determine end time based on whether in conversation
    if state.social_context.chatting_with:
        end_time = state.social_context.chatting_end_time
    else:
        start = action.start_time
        if start is None:
            return True
        
        # Round up to next minute if seconds != 0
        if start.second != 0:
            start = start.replace(second=0) + datetime.timedelta(minutes=1)
        
        duration = action.duration or 0
        end_time = start + datetime.timedelta(minutes=duration)
    
    if end_time is None:
        return True
    
    curr_time = state.world_context.curr_time
    if curr_time is None:
        return True
    
    return end_time.strftime("%H:%M:%S") == curr_time.strftime("%H:%M:%S")


def get_schedule_index(state: PersonaState, advance: int = 0) -> int:
    """
    Get the current index in f_daily_schedule based on elapsed time.
    
    The schedule is a list of (task, duration) tuples. This function
    finds which task should be active at the current time.
    
    Args:
        state: The persona's current state.
        advance: Minutes to look ahead (default 0).
        
    Returns:
        Index into f_daily_schedule for the current/upcoming task.
    """
    curr_time = state.world_context.curr_time
    if curr_time is None:
        return 0
    
    # Calculate minutes elapsed today
    today_min_elapsed = curr_time.hour * 60 + curr_time.minute + advance
    
    # Find the schedule slot
    elapsed = 0
    for idx, action in enumerate(state.executive_state.f_daily_schedule):
        elapsed += action.duration
        if elapsed > today_min_elapsed:
            return idx
    
    return len(state.executive_state.f_daily_schedule)


def get_hourly_schedule_index(state: PersonaState, advance: int = 0) -> int:
    """
    Get the current index in f_daily_schedule_hourly_org.
    
    Same as get_schedule_index but for the non-decomposed hourly schedule.
    
    Args:
        state: The persona's current state.
        advance: Minutes to look ahead (default 0).
        
    Returns:
        Index into f_daily_schedule_hourly_org.
    """
    curr_time = state.world_context.curr_time
    if curr_time is None:
        return 0
    
    today_min_elapsed = curr_time.hour * 60 + curr_time.minute + advance
    
    elapsed = 0
    for idx, action in enumerate(state.executive_state.f_daily_schedule_hourly_org):
        elapsed += action.duration
        if elapsed > today_min_elapsed:
            return idx
    
    return len(state.executive_state.f_daily_schedule_hourly_org)


def format_identity_summary(state: PersonaState) -> str:
    """
    Generate the ISS (Identity Stable Set) string.
    
    This is the core identity description used in most prompts.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Multi-line string with persona's identity information.
        
    Example:
        "Name: Dolores Heitmiller
         Age: 28
         Innate traits: hard-edged, independent, loyal
         ..."
    """
    identity = state.identity_profile.identity
    curr_time = state.world_context.curr_time
    daily_plan_req = state.executive_state.daily_plan_req
    
    date_str = curr_time.strftime('%A %B %d') if curr_time else 'Unknown'
    
    return f"""Name: {identity.name}
Age: {identity.age}
Innate traits: {identity.innate}
Learned traits: {identity.learned}
Currently: {identity.currently}
Lifestyle: {identity.lifestyle}
Daily plan requirement: {daily_plan_req}
Current Date: {date_str}"""


def format_action_time(state: PersonaState) -> str:
    """
    Format the action start time as a string.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Time string like "14:05 P.M." or empty string if no action.
    """
    start_time = state.action_state.current_action.start_time
    if start_time is None:
        return ""
    return start_time.strftime("%H:%M %p")


def get_current_event(state: PersonaState) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Get the current event triple (subject, predicate, object).
    
    Args:
        state: The persona's current state.
        
    Returns:
        Event tuple, or (name, None, None) if no action.
    """
    action = state.action_state.current_action
    name = state.identity_profile.identity.name
    
    if not action.address:
        return (name, None, None)
    return action.event


def get_current_event_and_desc(state: PersonaState) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    Get the current event triple plus description.
    
    Args:
        state: The persona's current state.
        
    Returns:
        (subject, predicate, object, description) tuple.
    """
    action = state.action_state.current_action
    name = state.identity_profile.identity.name
    
    if not action.address:
        return (name, None, None, None)
    
    return (
        action.event[0],
        action.event[1],
        action.event[2],
        action.description
    )


def get_current_obj_event_and_desc(state: PersonaState) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    Get the current object interaction event and description.
    
    Args:
        state: The persona's current state.
        
    Returns:
        (address, predicate, object, description) tuple.
    """
    action = state.action_state.current_action
    
    if not action.address:
        return ("", None, None, None)
    
    return (
        action.address,
        action.obj_event[1] if action.obj_event else None,
        action.obj_event[2] if action.obj_event else None,
        action.obj_description
    )


def format_action_summary(state: PersonaState) -> dict:
    """
    Create a dictionary summary of the current action.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Dictionary with action details.
    """
    action = state.action_state.current_action
    name = state.identity_profile.identity.name
    
    return {
        "persona": name,
        "address": action.address,
        "start_datetime": action.start_time,
        "duration": action.duration,
        "description": action.description,
        "pronunciatio": action.pronunciatio,
    }


def format_action_summary_str(state: PersonaState) -> str:
    """
    Create a human-readable string summary of the current action.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Multi-line string describing the action.
    """
    action = state.action_state.current_action
    name = state.identity_profile.identity.name
    
    if action.start_time is None:
        return f"Activity: {name} has no current action\n"
    
    start_str = action.start_time.strftime("%A %B %d -- %H:%M %p")
    
    return f"""[{start_str}]
Activity: {name} is {action.description}
Address: {action.address}
Duration in minutes (e.g., x min): {action.duration} min
"""


def format_daily_schedule_summary(state: PersonaState) -> str:
    """
    Format the daily schedule as a readable string.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Multi-line string with times and tasks.
    """
    lines = []
    curr_min_sum = 0
    
    for action in state.executive_state.f_daily_schedule:
        curr_min_sum += action.duration
        hour = curr_min_sum // 60
        minute = curr_min_sum % 60
        lines.append(f"{hour:02}:{minute:02} || {action.description}")
    
    return "\n".join(lines)


def format_hourly_schedule_summary(state: PersonaState) -> str:
    """
    Format the hourly (non-decomposed) schedule as a readable string.
    
    Args:
        state: The persona's current state.
        
    Returns:
        Multi-line string with times and tasks.
    """
    lines = []
    curr_min_sum = 0
    
    for action in state.executive_state.f_daily_schedule_hourly_org:
        curr_min_sum += action.duration
        hour = curr_min_sum // 60
        minute = curr_min_sum % 60
        lines.append(f"{hour:02}:{minute:02} || {action.description}")
    
    return "\n".join(lines)
