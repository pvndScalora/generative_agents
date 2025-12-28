"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: run_gpt_prompt.py
Description: Defines all run gpt prompt functions. These functions directly
interface with the safe_generate_response function.
"""
import re
import datetime
import sys
import ast
import random
import string
import json

sys.path.append('../../')

from persona.prompt_template.gpt_structure import (
    llm_service, 
    ChatGPT_safe_generate_response_OLD, 
    generate_prompt, 
    ChatGPT_single_request,
    DEBUG
)
from persona.prompt_template.print_prompt import print_run_prompts
from persona.prompt_template.prompts import (
    WakeUpHourPrompt,
    WakeUpHourInput,
    DailyPlanPrompt,
    DailyPlanInput,
    HourlySchedulePrompt,
    HourlyScheduleInput,
    TaskDecompPrompt,
    TaskDecompInput,
    ActionSectorPrompt,
    ActionSectorInput,
    ActionArenaPrompt,
    ActionArenaInput,
    ActionGameObjectPrompt,
    ActionGameObjectInput,
    PronunciatioPrompt,
    PronunciatioInput,
    EventTriplePrompt,
    EventTripleInput,
    ActObjDescPrompt,
    ActObjDescInput,
    ActObjEventTriplePrompt,
    ActObjEventTripleInput,
    NewDecompSchedulePrompt,
    NewDecompScheduleInput,
    DecideToTalkPrompt,
    DecideToTalkInput,
    DecideToReactPrompt,
    DecideToReactInput,
    CreateConversationPrompt,
    CreateConversationInput,
    SummarizeConversationPrompt,
    SummarizeConversationInput,
    ExtractKeywordsPrompt,
    ExtractKeywordsInput,
    KeywordToThoughtsPrompt,
    KeywordToThoughtsInput,
    ConvoToThoughtsPrompt,
    ConvoToThoughtsInput,
    EventPoignancyPrompt,
    EventPoignancyInput,
    ThoughtPoignancyPrompt,
    ThoughtPoignancyInput,
    ChatPoignancyPrompt,
    ChatPoignancyInput,
    FocalPtPrompt,
    FocalPtInput,
    InsightAndGuidancePrompt,
    InsightAndGuidanceInput,
    AgentChatSummarizeIdeasPrompt,
    AgentChatSummarizeIdeasInput,
    AgentChatSummarizeRelationshipPrompt,
    AgentChatSummarizeRelationshipInput,
    AgentChatPrompt,
    AgentChatInput,
    SummarizeIdeasPrompt,
    SummarizeIdeasInput,
    GenerateNextConvoLinePrompt,
    GenerateNextConvoLineInput,
    WhisperInnerThoughtPrompt,
    WhisperInnerThoughtInput,
    PlanningThoughtOnConvoPrompt,
    PlanningThoughtOnConvoInput,
    MemoOnConvoPrompt,
    MemoOnConvoInput,
)
from persona.prompt_template.executor import PromptExecutor

# Initialize the executor with the service from gpt_structure
prompt_executor = PromptExecutor(llm_service)

def get_random_alphanumeric(i=6, j=6): 
  """
  Returns a random alpha numeric strength that has the length of somewhere
  between i and j. 

  INPUT: 
    i: min_range for the length
    j: max_range for the length
  OUTPUT: 
    an alpha numeric str with the length of somewhere between i and j.
  """
  k = random.randint(i, j)
  x = ''.join(random.choices(string.ascii_letters + string.digits, k=k))
  return x

def safe_execute_prompt(prompt_instance, gpt_param, input_data=None, verbose=False):
  """
  Execute a prompt using the new schema-based system.
  
  Args:
    prompt_instance: The prompt class (not instance) for new-style prompts
    gpt_param: GPT parameters dict
    input_data: Input data (dict or Pydantic model) for the prompt
    verbose: Whether to print debug info
  """
  # Map legacy parameters
  model = gpt_param.get("engine", "gpt-3.5-turbo-instruct")
  if model == "text-davinci-003":
      model = "gpt-3.5-turbo-instruct"
      
  # Extract other parameters
  temperature = gpt_param.get("temperature", 0.7)
  max_tokens = gpt_param.get("max_tokens", None)
  
  # Filter out keys that are not for the LLM call or need mapping
  kwargs = {k: v for k, v in gpt_param.items() if k not in ["engine", "temperature", "max_tokens"]}

  # Check if this is a new-style prompt (class with input_schema)
  is_new_style = hasattr(prompt_instance, 'input_schema')
  
  if is_new_style:
    # New-style prompt: instantiate the prompt class
    prompt = prompt_instance()
    
    output = prompt_executor.execute(
        prompt,
        input_data,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Generate prompt text for debugging
    prompt_text = prompt_executor._generate_prompt_text(prompt, input_data)
    fail_safe = prompt.get_fail_safe()
    
    if DEBUG or verbose: 
      print(f"=== Prompt ===\n{prompt_text}\n=== Output ===\n{output}")
      
    return output, [output, prompt_text, gpt_param, input_data, fail_safe]
  else:
    # Legacy prompt instance
    output = prompt_executor.execute(
        prompt_instance,
        input_data,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Reconstruct debug info
    prompt_input = prompt_instance.create_prompt_input(input_data)
    prompt_text = prompt_executor._generate_prompt_text(prompt_instance, input_data)
    fail_safe = prompt_instance.get_fail_safe()
    
    if DEBUG or prompt_instance.verbose: 
      print_run_prompts(prompt_instance.prompt_template, prompt_instance.persona, gpt_param, 
                        prompt_input, prompt_text, output)
      
    return output, [output, prompt_text, gpt_param, prompt_input, fail_safe]

def get_gpt_param(override_params=None):
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 50, 
               "temperature": 0.0, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  if override_params:
    for k, v in override_params.items():
      gpt_param[k] = v
  return gpt_param


##############################################################################
# CHAPTER 1: Run GPT Prompt
##############################################################################

def run_gpt_prompt_wake_up_hour(persona, test_input=None, verbose=False): 
  """
  Given the persona, returns an integer that indicates the hour when the 
  persona wakes up.  

  INPUT: 
    persona: The Persona class instance 
  OUTPUT: 
    integer for the wake up hour.
  """
  gpt_param = get_gpt_param({"max_tokens": 5, "temperature": 0.8})
  
  # Build input data for the new schema-based prompt
  if test_input is None:
    input_data = WakeUpHourInput(
      identity_stable_set=persona.scratch.get_str_iss(),
      lifestyle=persona.scratch.get_str_lifestyle(),
      first_name=persona.scratch.get_str_firstname()
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(WakeUpHourPrompt, gpt_param, input_data, verbose)
  
  # Extract hour from output (which is WakeUpHourOutput)
  if hasattr(output, 'hour'):
    return output.hour, debug_info
  else:
    # Fallback for raw string output
    return int(str(output).strip().lower().split("am")[0]), debug_info


def run_gpt_prompt_daily_plan(persona, 
                              wake_up_hour, 
                              test_input=None, 
                              verbose=False):
  """
  Basically the long term planning that spans a day. Returns a list of actions
  that the persona will take today. Usually comes in the following form: 
  'wake up and complete the morning routine at 6:00 am', 
  'eat breakfast at 7:00 am',.. 
  Note that the actions come without a period. 

  INPUT: 
    persona: The Persona class instance 
  OUTPUT: 
    a list of daily actions in broad strokes.
  """
  gpt_param = get_gpt_param({"max_tokens": 500, "temperature": 1, "stop": None})
  
  if test_input is None:
    input_data = DailyPlanInput(
      identity_stable_set=persona.get_str_iss(),
      lifestyle=persona.get_str_lifestyle(),
      current_date=persona.get_str_curr_date_str(),
      first_name=persona.get_str_firstname(),
      wake_up_hour=f"{wake_up_hour}:00 am"
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(DailyPlanPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'activities'):
    # Prepend wake up activity
    activities = [f"wake up and complete the morning routine at {wake_up_hour}:00 am"] + output.activities
    return activities, debug_info
  else:
    return output, debug_info


def run_gpt_prompt_generate_hourly_schedule(persona, 
                                            curr_hour_str, 
                                            p_f_ds_hourly_org, 
                                            hour_str,
                                            intermission2=None,
                                            test_input=None, 
                                            verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "temperature": 0.5, "stop": ["\n"]})
  
  if test_input is None:
    # Convert inputs to strings
    prior_schedule_str = str(p_f_ds_hourly_org) if p_f_ds_hourly_org else ""
    hour_str_val = str(hour_str) if hour_str else ""
    
    input_data = HourlyScheduleInput(
      schedule_format=persona.get_str_schedule_format() if hasattr(persona, 'get_str_schedule_format') else "",
      identity_stable_set=persona.get_str_iss(),
      prior_schedule=prior_schedule_str,
      daily_plan_req=persona.get_str_daily_plan_req() if hasattr(persona, 'get_str_daily_plan_req') else "",
      intermission=str(intermission2) if intermission2 else "",
      prompt_ending=hour_str_val
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(HourlySchedulePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'activity'):
    return output.activity, debug_info
  return output, debug_info


def run_gpt_prompt_task_decomp(persona, 
                               task, 
                               duration, 
                               test_input=None, 
                               verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 1000, "stop": None})
  
  if test_input is None:
    input_data = TaskDecompInput(
      identity_stable_set=persona.get_str_iss(),
      schedule_summary=persona.get_str_schedule_summary() if hasattr(persona, 'get_str_schedule_summary') else "",
      first_name=persona.get_str_firstname(),
      task=task,
      time_range=f"{duration} minutes",
      duration_minutes=duration
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(TaskDecompPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'subtasks'):
    # Convert to legacy format: list of [activity, duration] pairs
    result = [[s.description, s.duration_minutes] for s in output.subtasks]
    return result, debug_info
  return output, debug_info


def run_gpt_prompt_action_sector(action_description, 
                                persona, 
                                maze, 
                                test_input=None, 
                                verbose=False):
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  # Get accessible sectors from the persona's spatial memory (what they know)
  accessible_sectors = []
  if hasattr(persona, 's_mem') and hasattr(persona.s_mem, 'tree'):
    try:
      # Get all sectors the persona knows about across all worlds they know
      for world in persona.s_mem.tree.values():
        if isinstance(world, dict):
          accessible_sectors.extend(world.keys())
    except (AttributeError, TypeError):
      pass
  
  # Fallback to maze if persona has no spatial memory
  if not accessible_sectors and hasattr(maze, 'get_accessible_sectors'):
    accessible_sectors = maze.get_accessible_sectors()
  
  if test_input is None:
    # Extract action detail from parentheses if present
    action_detail = ""
    if "(" in action_description and ")" in action_description:
      action_detail = action_description[action_description.find("(")+1:action_description.find(")")]
    
    # Get living area info - it should already be in "world:sector" format
    living_area = persona.living_area if hasattr(persona, 'living_area') else ""
    living_area_arenas = ""
    if living_area and hasattr(persona, 's_mem') and hasattr(persona.s_mem, 'get_str_accessible_sector_arenas'):
      try:
        living_area_arenas = persona.s_mem.get_str_accessible_sector_arenas(living_area)
      except (ValueError, KeyError):
        living_area_arenas = ""
    
    # Get current sector info from tile
    current_world = ""
    current_sector = ""
    current_sector_arenas = ""
    curr_tile = persona.curr_tile if hasattr(persona, 'curr_tile') else None
    if curr_tile and hasattr(maze, 'access_tile'):
      try:
        tile_info = maze.access_tile(curr_tile)
        if tile_info:
          current_world = tile_info.get("world", "")
          current_sector = tile_info.get("sector", "")
          if current_world and current_sector and hasattr(persona, 's_mem'):
            sector_path = f"{current_world}:{current_sector}"
            try:
              current_sector_arenas = persona.s_mem.get_str_accessible_sector_arenas(sector_path)
            except (ValueError, KeyError):
              current_sector_arenas = ""
      except (IndexError, KeyError, TypeError):
        pass
    
    # Get daily_plan_req safely as string
    daily_plan_req_val = ""
    if hasattr(persona, 'daily_req'):
      daily_plan_req_val = str(persona.daily_req) if persona.daily_req else ""
    
    input_data = ActionSectorInput(
      persona_name=persona.name if hasattr(persona, 'name') else (persona.get_str_firstname() if hasattr(persona, 'get_str_firstname') else ""),
      living_area=str(living_area) if living_area else "",
      living_area_arenas=str(living_area_arenas) if living_area_arenas else "",
      current_sector=str(current_sector) if current_sector else "",
      current_sector_arenas=str(current_sector_arenas) if current_sector_arenas else "",
      daily_plan_req=daily_plan_req_val,
      accessible_sectors=", ".join(accessible_sectors) if accessible_sectors else "",
      action_description=str(action_description) if action_description else "",
      action_detail=str(action_detail) if action_detail else ""
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ActionSectorPrompt, gpt_param, input_data, verbose)
  
  # Validate and extract the sector
  result_sector = output.sector if hasattr(output, 'sector') else str(output)
  
  # Clean up the result - strip quotes, extra whitespace, and common punctuation
  result_sector = result_sector.strip().strip('"\'\'').strip()
  
  # Try to match against accessible sectors - find which sector name appears in the response
  if accessible_sectors:
    result_sector_lower = result_sector.lower()
    
    # First try exact match (case-insensitive)
    for sector in accessible_sectors:
      if sector.lower() == result_sector_lower:
        return sector, debug_info
    
    # Then try to find if any accessible sector is contained in the response
    for sector in accessible_sectors:
      if sector.lower() in result_sector_lower:
        return sector, debug_info
    
    # Try the reverse - check if the result contains any of the sectors
    # This handles cases like "bathroom to brush" when sector is "bathroom"
    for sector in accessible_sectors:
      # Check if the result starts with the sector name
      if result_sector_lower.startswith(sector.lower()):
        return sector, debug_info
      # Check if sector name appears as a word in the result
      import re
      if re.search(r'\b' + re.escape(sector.lower()) + r'\b', result_sector_lower):
        return sector, debug_info
    
    # If no match found, return the first accessible sector as fallback
    if accessible_sectors:
      return accessible_sectors[0], debug_info
  
  return result_sector, debug_info


def run_gpt_prompt_action_arena(action_description, 
                                persona, 
                                maze, act_world, act_sector,
                                test_input=None, 
                                verbose=False):
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  # Get accessible arenas from the persona's spatial memory (what they know)
  # NOT from the maze (what physically exists)
  accessible_arenas = []
  if hasattr(persona, 's_mem') and hasattr(persona.s_mem, 'tree'):
    try:
      sector_path = f"{act_world}:{act_sector}"
      # Get the arenas the persona knows about in this sector
      if act_world in persona.s_mem.tree and act_sector in persona.s_mem.tree[act_world]:
        accessible_arenas = list(persona.s_mem.tree[act_world][act_sector].keys())
    except (KeyError, AttributeError, TypeError):
      pass
  
  # Fallback to maze if persona has no spatial memory
  if not accessible_arenas and hasattr(maze, 'get_accessible_arenas'):
    accessible_arenas = maze.get_accessible_arenas(act_world, act_sector)
    if accessible_arenas is None:
      accessible_arenas = []
  
  if test_input is None:
    action_detail = ""
    if "(" in action_description and ")" in action_description:
      action_detail = action_description[action_description.find("(")+1:action_description.find(")")]
      
    input_data = ActionArenaInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      sector=act_sector,
      accessible_arenas=", ".join(accessible_arenas) if accessible_arenas else "",
      action_description=action_description,
      action_detail=action_detail
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ActionArenaPrompt, gpt_param, input_data, verbose)
  
  # Validate and extract the arena
  result_arena = output.arena if hasattr(output, 'arena') else str(output)
  
  # Clean up the result - strip quotes, extra whitespace, and common punctuation
  result_arena = result_arena.strip().strip('"\'\'').strip()
  
  # Try to match against accessible arenas - find which arena name appears in the response
  if accessible_arenas:
    result_arena_lower = result_arena.lower()
    
    # First try exact match (case-insensitive)
    for arena in accessible_arenas:
      if arena.lower() == result_arena_lower:
        return arena, debug_info
    
    # Then try to find if any accessible arena is contained in the response
    for arena in accessible_arenas:
      if arena.lower() in result_arena_lower:
        return arena, debug_info
    
    # Try the reverse - check if the result contains any of the arenas
    # This handles cases like "sink area in the bathroom to brush their teeth"
    for arena in accessible_arenas:
      # Check if the result starts with the arena name
      if result_arena_lower.startswith(arena.lower()):
        return arena, debug_info
      # Check if arena name appears as a word in the result
      import re
      if re.search(r'\b' + re.escape(arena.lower()) + r'\b', result_arena_lower):
        return arena, debug_info
    
    # If no match found, return the first accessible arena as fallback
    if accessible_arenas:
      return accessible_arenas[0], debug_info
  
  return result_arena, debug_info


def run_gpt_prompt_action_game_object(action_description, 
                                      persona, 
                                      maze,
                                      temp_address,
                                      test_input=None, 
                                      verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  # Get accessible objects for validation
  accessible_objects = []
  if hasattr(maze, 'get_accessible_objects'):
    accessible_objects = maze.get_accessible_objects(temp_address)
    if accessible_objects is None:
      accessible_objects = []
  
  if test_input is None:
    input_data = ActionGameObjectInput(
      action_description=action_description,
      accessible_objects=", ".join(accessible_objects) if accessible_objects else ""
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ActionGameObjectPrompt, gpt_param, input_data, verbose)
  
  # Validate and extract the game object
  result_obj = output.game_object if hasattr(output, 'game_object') else str(output)
  
  # Try to match against accessible objects - find which object name appears in the response
  if accessible_objects:
    result_obj_lower = result_obj.lower()
    # First try exact match
    for obj in accessible_objects:
      if obj.lower() == result_obj_lower:
        return obj, debug_info
    # Then try to find which object is mentioned in the response
    for obj in accessible_objects:
      if obj.lower() in result_obj_lower:
        return obj, debug_info
    # If no match, return the first accessible object as fallback
    return accessible_objects[0], debug_info
  
  return result_obj, debug_info


def run_gpt_prompt_pronunciatio(action_description, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  input_data = PronunciatioInput(action_description=action_description)
  output, debug_info = safe_execute_prompt(PronunciatioPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'emoji'):
    return output.emoji, debug_info
  return output, debug_info


def run_gpt_prompt_event_triple(action_description, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 30, "stop": ["\n"]})
  
  input_data = EventTripleInput(
    persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
    action_description=action_description
  )
  output, debug_info = safe_execute_prompt(EventTriplePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'subject'):
    return (output.subject, output.predicate, output.object), debug_info
  return output, debug_info


def run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  input_data = ActObjDescInput(
    game_object=act_game_object,
    persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
    action_description=act_desp
  )
  output, debug_info = safe_execute_prompt(ActObjDescPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'object_state'):
    return output.object_state, debug_info
  return output, debug_info


def run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 30, "stop": ["\n"]})
  
  input_data = ActObjEventTripleInput(
    game_object=act_game_object,
    object_description=act_obj_desc
  )
  output, debug_info = safe_execute_prompt(ActObjEventTriplePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'subject'):
    return (output.subject, output.predicate, output.object), debug_info
  return output, debug_info


def run_gpt_prompt_new_decomp_schedule(persona, 
                                       main_act_dur, 
                                       truncated_act_dur, 
                                       start_time_hour,
                                       end_time_hour, 
                                       inserted_act,
                                       inserted_act_dur,
                                       test_input=None, 
                                       verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 1000, "stop": None})
  
  if test_input is None:
    input_data = NewDecompScheduleInput(
      identity_stable_set=persona.get_str_iss(),
      schedule_summary=f"From {start_time_hour} to {end_time_hour}",
      first_name=persona.get_str_firstname(),
      current_task=inserted_act,
      remaining_duration=inserted_act_dur
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(NewDecompSchedulePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'subtasks'):
    result = [[s.description, s.duration_minutes] for s in output.subtasks]
    return result, debug_info
  return output, debug_info


def run_gpt_prompt_decide_to_talk(persona, target_persona, retrieved, test_input=None, 
                                       verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 20, "stop": None})
  
  if test_input is None:
    input_data = DecideToTalkInput(
      context=str(retrieved) if retrieved else "",
      current_time=str(persona.curr_time) if hasattr(persona, 'curr_time') else "",
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      target_name=target_persona.name if hasattr(target_persona, 'name') else str(target_persona),
      last_chatted_time="",
      last_chat_about="",
      persona_activity=persona.get_curr_action() if hasattr(persona, 'get_curr_action') else "",
      target_activity=target_persona.get_curr_action() if hasattr(target_persona, 'get_curr_action') else ""
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(DecideToTalkPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'should_talk'):
    return output.should_talk, debug_info
  return output, debug_info


def run_gpt_prompt_decide_to_react(persona, target_persona, retrieved, test_input=None, 
                                       verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 20, "stop": None})
  
  if test_input is None:
    input_data = DecideToReactInput(
      context=str(retrieved) if retrieved else "",
      current_time=str(persona.curr_time) if hasattr(persona, 'curr_time') else "",
      persona_activity=persona.get_curr_action() if hasattr(persona, 'get_curr_action') else "",
      target_activity=target_persona.get_curr_action() if hasattr(target_persona, 'get_curr_action') else "",
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      persona_action="",
      target_name=target_persona.name if hasattr(target_persona, 'name') else str(target_persona),
      target_action=""
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(DecideToReactPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'option'):
    return output.option, debug_info
  return output, debug_info


def run_gpt_prompt_create_conversation(persona, target_persona, curr_loc,
                                       test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 1000, "temperature": 0.7, "stop": None})
  
  if test_input is None:
    input_data = CreateConversationInput(
      current_date=persona.get_str_curr_date_str() if hasattr(persona, 'get_str_curr_date_str') else "",
      location=curr_loc,
      previous_conversation_context="",
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      target_name=target_persona.name if hasattr(target_persona, 'name') else str(target_persona),
      persona_identity=persona.get_str_iss() if hasattr(persona, 'get_str_iss') else "",
      target_identity=target_persona.get_str_iss() if hasattr(target_persona, 'get_str_iss') else ""
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(CreateConversationPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'conversation'):
    result = [[turn.speaker, turn.utterance] for turn in output.conversation]
    return result, debug_info
  return output, debug_info


def run_gpt_prompt_summarize_conversation(persona, conversation, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    convo_text = "\n".join([f"{s}: {u}" for s, u in conversation]) if isinstance(conversation, list) else str(conversation)
    input_data = SummarizeConversationInput(conversation_text=convo_text)
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(SummarizeConversationPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'summary'):
    return output.summary, debug_info
  return output, debug_info


def run_gpt_prompt_extract_keywords(persona, description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  
  if test_input is None:
    input_data = ExtractKeywordsInput(description=description)
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ExtractKeywordsPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'keywords'):
    return output.keywords, debug_info
  return output, debug_info


def run_gpt_prompt_keyword_to_thoughts(persona, keyword, concept_summary, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 40, "temperature": 0.7, "stop": None})
  
  if test_input is None:
    input_data = KeywordToThoughtsInput(
      keyword=keyword,
      concept_summary=concept_summary,
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname()
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(KeywordToThoughtsPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'thought'):
    return output.thought, debug_info
  return output, debug_info


def run_gpt_prompt_convo_to_thoughts(persona, 
                                    init_persona_name,  
                                    target_persona_name,
                                    convo_str,
                                    fin_target, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 40, "temperature": 0.7, "stop": None})
  
  if test_input is None:
    input_data = ConvoToThoughtsInput(
      init_persona_name=init_persona_name,
      target_persona_name=target_persona_name,
      conversation_text=convo_str,
      target_for_thought=fin_target
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ConvoToThoughtsPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'thought'):
    return output.thought, debug_info
  return output, debug_info


def run_gpt_prompt_event_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = EventPoignancyInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      identity_stable_set=persona.get_str_iss() if hasattr(persona, 'get_str_iss') else "",
      event_description=event_description
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(EventPoignancyPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'rating'):
    return output.rating, debug_info
  return output, debug_info


def run_gpt_prompt_thought_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = ThoughtPoignancyInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      identity_stable_set=persona.get_str_iss() if hasattr(persona, 'get_str_iss') else "",
      thought_description=event_description
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ThoughtPoignancyPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'rating'):
    return output.rating, debug_info
  return output, debug_info


def run_gpt_prompt_chat_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = ChatPoignancyInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      identity_stable_set=persona.get_str_iss() if hasattr(persona, 'get_str_iss') else "",
      chat_description=event_description
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(ChatPoignancyPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'rating'):
    return output.rating, debug_info
  return output, debug_info


def run_gpt_prompt_focal_pt(persona, statements, n, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = FocalPtInput(
      statements=statements,
      num_questions=n
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(FocalPtPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'questions'):
    return output.questions, debug_info
  return output, debug_info


def run_gpt_prompt_insight_and_guidance(persona, statements, n, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 150, "temperature": 0.5, "stop": None})
  
  if test_input is None:
    input_data = InsightAndGuidanceInput(
      statements=statements,
      num_insights=n
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(InsightAndGuidancePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'insights'):
    return output.insights, debug_info
  return output, debug_info


def run_gpt_prompt_agent_chat_summarize_ideas(persona, target_persona, statements, curr_context, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = AgentChatSummarizeIdeasInput(
      statements=statements,
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      question=curr_context
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(AgentChatSummarizeIdeasPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'summary'):
    return output.summary, debug_info
  return output, debug_info


def run_gpt_prompt_agent_chat_summarize_relationship(persona, target_persona, statements, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = AgentChatSummarizeRelationshipInput(
      statements=statements,
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      target_name=target_persona.name if hasattr(target_persona, 'name') else str(target_persona)
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(AgentChatSummarizeRelationshipPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'relationship'):
    return output.relationship, debug_info
  return output, debug_info


def run_gpt_prompt_agent_chat(maze, persona, target_persona,
                               curr_context, 
                               init_summ_idea, 
                               target_summ_idea, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = AgentChatInput(
      persona_currently=persona.get_curr_action() if hasattr(persona, 'get_curr_action') else "",
      target_currently=target_persona.get_curr_action() if hasattr(target_persona, 'get_curr_action') else "",
      previous_conversation_context="",
      current_context=curr_context,
      current_location="",
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      persona_summary_idea=init_summ_idea,
      target_name=target_persona.name if hasattr(target_persona, 'name') else str(target_persona),
      target_summary_idea=target_summ_idea
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(AgentChatPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'conversation'):
    result = [[turn.speaker, turn.utterance] for turn in output.conversation]
    return result, debug_info
  return output, debug_info


def run_gpt_prompt_summarize_ideas(persona, statements, question, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = SummarizeIdeasInput(
      statements=statements,
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      question=question
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(SummarizeIdeasPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'summary'):
    return output.summary, debug_info
  return output, debug_info


def run_gpt_prompt_generate_next_convo_line(persona, interlocutor_desc, prev_convo, retrieved_summary, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 250, "temperature": 1, "stop": None})
  
  if test_input is None:
    input_data = GenerateNextConvoLineInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      persona_identity=persona.get_str_iss() if hasattr(persona, 'get_str_iss') else "",
      interlocutor_desc=interlocutor_desc,
      previous_conversation=prev_convo,
      retrieved_summary=retrieved_summary
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(GenerateNextConvoLinePrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'utterance'):
    return output.utterance, debug_info
  return output, debug_info


def run_gpt_prompt_generate_whisper_inner_thought(persona, whisper, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  
  if test_input is None:
    input_data = WhisperInnerThoughtInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      whisper=whisper
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(WhisperInnerThoughtPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'inner_thought'):
    return output.inner_thought, debug_info
  return output, debug_info


def run_gpt_prompt_planning_thought_on_convo(persona, all_utt, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  
  if test_input is None:
    input_data = PlanningThoughtOnConvoInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      conversation_summary=all_utt
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(PlanningThoughtOnConvoPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'thought'):
    return output.thought, debug_info
  return output, debug_info


def run_gpt_prompt_memo_on_convo(persona, all_utt, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  
  if test_input is None:
    input_data = MemoOnConvoInput(
      persona_name=persona.name if hasattr(persona, 'name') else persona.get_str_firstname(),
      conversation_summary=all_utt,
      target_name=""  # This would need to be extracted
    )
  else:
    input_data = test_input
    
  output, debug_info = safe_execute_prompt(MemoOnConvoPrompt, gpt_param, input_data, verbose)
  
  if hasattr(output, 'memo'):
    return output.memo, debug_info
  return output, debug_info


def run_gpt_generate_safety_score(persona, comment, test_input=None, verbose=False): 
  def create_prompt_input(comment, test_input=None):
    prompt_input = [comment]
    return prompt_input

  def __chat_func_clean_up(gpt_response, prompt=""): 
    gpt_response = json.loads(gpt_response)
    return gpt_response["output"]

  def __chat_func_validate(gpt_response, prompt=""): 
    try: 
      fields = ["output"]
      response = json.loads(gpt_response)
      for field in fields: 
        if field not in response: 
          return False
      return True
    except:
      return False 

  def get_fail_safe():
    return None

  print ("11")
  prompt_template = "persona/prompt_template/safety/anthromorphosization_v1.txt" 
  prompt_input = create_prompt_input(comment) 
  print ("22")
  prompt = generate_prompt(prompt_input, prompt_template)
  print (prompt)
  fail_safe = get_fail_safe() 
  output = ChatGPT_safe_generate_response_OLD(prompt, 3, fail_safe,
                        __chat_func_validate, __chat_func_clean_up, verbose)
  print (output)
  
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 50, 
               "temperature": 0, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def extract_first_json_dict(data_str):
    # Find the first occurrence of a JSON object within the string
    start_idx = data_str.find('{')
    end_idx = data_str.find('}', start_idx) + 1

    # Check if both start and end indices were found
    if start_idx == -1 or end_idx == 0:
        return None

    # Extract the first JSON dictionary
    json_str = data_str[start_idx:end_idx]

    try:
        # Attempt to parse the JSON data
        json_dict = json.loads(json_str)
        return json_dict
    except json.JSONDecodeError:
        # If parsing fails, return None
        return None


def run_gpt_generate_iterative_chat_utt(maze, init_persona, target_persona, retrieved, curr_context, curr_chat, test_input=None, verbose=False): 
  def create_prompt_input(maze, init_persona, target_persona, retrieved, curr_context, curr_chat, test_input=None):
    persona = init_persona
    prev_convo_insert = "\n"
    if persona.a_mem.seq_chat: 
      for i in persona.a_mem.seq_chat: 
        if i.object == target_persona.scratch.name: 
          v1 = int((persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, {persona.scratch.name} and {target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if persona.a_mem.seq_chat: 
      if int((persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""
    print (prev_convo_insert)

    curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
    curr_location = f"{curr_arena} in {curr_sector}"

    retrieved_str = ""
    for key, vals in retrieved.items(): 
      for v in vals: 
        retrieved_str += f"- {v.description}\n"


    convo_str = ""
    for i in curr_chat:
      convo_str += ": ".join(i) + "\n"
    if convo_str == "": 
      convo_str = "[The conversation has not started yet -- start it!]"

    init_iss = f"Here is Here is a brief description of {init_persona.scratch.name}.\n{init_persona.scratch.get_str_iss()}"
    prompt_input = [init_iss, init_persona.scratch.name, retrieved_str, prev_convo_insert,
      curr_location, curr_context, init_persona.scratch.name, target_persona.scratch.name,
      convo_str, init_persona.scratch.name, target_persona.scratch.name,
      init_persona.scratch.name, init_persona.scratch.name,
      init_persona.scratch.name
      ]
    return prompt_input

  def __chat_func_clean_up(gpt_response, prompt=""): 
    gpt_response = extract_first_json_dict(gpt_response)

    cleaned_dict = dict()
    cleaned = []
    for key, val in gpt_response.items(): 
      cleaned += [val]
    cleaned_dict["utterance"] = cleaned[0]
    cleaned_dict["end"] = True
    if "f" in str(cleaned[1]) or "F" in str(cleaned[1]): 
      cleaned_dict["end"] = False

    return cleaned_dict

  def __chat_func_validate(gpt_response, prompt=""): 
    print ("ugh...")
    try: 
      # print ("DEBUG 1")
      # print (gpt_response)
      # print ("DEBUG 2")

      print (extract_first_json_dict(gpt_response))
      # print ("DEBUG 3")

      return True
    except:
      return False 

  def get_fail_safe():
    cleaned_dict = dict()
    cleaned_dict["utterance"] = "..."
    cleaned_dict["end"] = False
    return cleaned_dict

  print ("11")
  prompt_template = "persona/prompt_template/v3_ChatGPT/iterative_convo_v1.txt" 
  prompt_input = create_prompt_input(maze, init_persona, target_persona, retrieved, curr_context, curr_chat) 
  print ("22")
  prompt = generate_prompt(prompt_input, prompt_template)
  print (prompt)
  fail_safe = get_fail_safe() 
  output = ChatGPT_safe_generate_response_OLD(prompt, 3, fail_safe,
                        __chat_func_validate, __chat_func_clean_up, verbose)
  print (output)
  
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 50, 
               "temperature": 0, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
