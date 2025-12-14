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

from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *
from persona.prompt_template.prompts import *

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

def safe_execute_prompt(prompt_instance, gpt_param, test_input=None):
  prompt_input = prompt_instance.create_prompt_input(test_input)
  prompt = generate_prompt(prompt_input, prompt_instance.prompt_template)
  fail_safe = prompt_instance.get_fail_safe()

  if prompt_instance.example_output is not None and prompt_instance.special_instruction is not None:
    output = ChatGPT_safe_generate_response(prompt, prompt_instance.example_output, prompt_instance.special_instruction, 3, fail_safe,
                                            prompt_instance.validate, prompt_instance.clean_up, True)
  else:
    output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                     prompt_instance.validate, prompt_instance.clean_up)
  
  if DEBUG or prompt_instance.verbose: 
    print_run_prompts(prompt_instance.prompt_template, prompt_instance.persona, gpt_param, 
                      prompt_input, prompt, output)
    
  return output, [output, prompt, gpt_param, prompt_input, fail_safe]

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
  prompt = WakeUpHourPrompt(persona, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


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
  prompt = DailyPlanPrompt(persona, wake_up_hour, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_generate_hourly_schedule(persona, 
                                            curr_hour_str, 
                                            p_f_ds_hourly_org, 
                                            hour_str,
                                            intermission2=None,
                                            test_input=None, 
                                            verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "temperature": 0.5, "stop": ["\n"]})
  prompt = HourlySchedulePrompt(persona, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_task_decomp(persona, 
                               task, 
                               duration, 
                               test_input=None, 
                               verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 1000, "stop": None})
  prompt = TaskDecompPrompt(persona, task, duration, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_action_sector(action_description, 
                                persona, 
                                maze, 
                                test_input=None, 
                                verbose=False):
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ActionSectorPrompt(persona, maze, action_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_action_arena(action_description, 
                                persona, 
                                maze, act_world, act_sector,
                                test_input=None, 
                                verbose=False):
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ActionArenaPrompt(persona, maze, act_world, act_sector, action_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_action_game_object(action_description, 
                                      persona, 
                                      maze,
                                      temp_address,
                                      test_input=None, 
                                      verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ActionGameObjectPrompt(persona, maze, temp_address, action_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_pronunciatio(action_description, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = PronunciatioPrompt(persona, action_description, verbose)
  return safe_execute_prompt(prompt, gpt_param)


def run_gpt_prompt_event_triple(action_description, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 30, "stop": ["\n"]})
  prompt = EventTriplePrompt(persona, action_description, verbose)
  return safe_execute_prompt(prompt, gpt_param)


def run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ActObjDescPrompt(persona, act_game_object, act_desp, verbose)
  return safe_execute_prompt(prompt, gpt_param)


def run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, persona, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 30, "stop": ["\n"]})
  prompt = ActObjEventTriplePrompt(persona, act_game_object, act_obj_desc, verbose)
  return safe_execute_prompt(prompt, gpt_param)


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
  prompt = NewDecompSchedulePrompt(persona, main_act_dur, truncated_act_dur, start_time_hour, end_time_hour, inserted_act, inserted_act_dur, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_decide_to_talk(persona, target_persona, retrieved,test_input=None, 
                                       verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 20, "stop": None})
  prompt = DecideToTalkPrompt(persona, target_persona, retrieved, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_decide_to_react(persona, target_persona, retrieved,test_input=None, 
                                       verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 20, "stop": None})
  prompt = DecideToReactPrompt(persona, target_persona, retrieved, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_create_conversation(persona, target_persona, curr_loc,
                                       test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 1000, "temperature": 0.7, "stop": None})
  prompt = CreateConversationPrompt(persona, target_persona, curr_loc, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_summarize_conversation(persona, conversation, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = SummarizeConversationPrompt(persona, conversation, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_extract_keywords(persona, description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  prompt = ExtractKeywordsPrompt(persona, description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_keyword_to_thoughts(persona, keyword, concept_summary, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 40, "temperature": 0.7, "stop": None})
  prompt = KeywordToThoughtsPrompt(persona, keyword, concept_summary, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_convo_to_thoughts(persona, 
                                    init_persona_name,  
                                    target_persona_name,
                                    convo_str,
                                    fin_target, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 40, "temperature": 0.7, "stop": None})
  prompt = ConvoToThoughtsPrompt(persona, init_persona_name, target_persona_name, convo_str, fin_target, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_event_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = EventPoignancyPrompt(persona, event_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_thought_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ThoughtPoignancyPrompt(persona, event_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_chat_poignancy(persona, event_description, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = ChatPoignancyPrompt(persona, event_description, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_focal_pt(persona, statements, n, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = FocalPtPrompt(persona, statements, n, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_insight_and_guidance(persona, statements, n, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 150, "temperature": 0.5, "stop": None})
  prompt = InsightAndGuidancePrompt(persona, statements, n, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_agent_chat_summarize_ideas(persona, target_persona, statements, curr_context, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = AgentChatSummarizeIdeasPrompt(persona, target_persona, statements, curr_context, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_agent_chat_summarize_relationship(persona, target_persona, statements, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = AgentChatSummarizeRelationshipPrompt(persona, target_persona, statements, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_agent_chat(maze, persona, target_persona,
                               curr_context, 
                               init_summ_idea, 
                               target_summ_idea, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = AgentChatPrompt(persona, maze, target_persona, curr_context, init_summ_idea, target_summ_idea, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_summarize_ideas(persona, statements, question, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = SummarizeIdeasPrompt(persona, statements, question, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_generate_next_convo_line(persona, interlocutor_desc, prev_convo, retrieved_summary, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 250, "temperature": 1, "stop": None})
  prompt = GenerateNextConvoLinePrompt(persona, interlocutor_desc, prev_convo, retrieved_summary, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_generate_whisper_inner_thought(persona, whisper, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  prompt = WhisperInnerThoughtPrompt(persona, whisper, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_planning_thought_on_convo(persona, all_utt, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 50, "stop": None})
  prompt = PlanningThoughtOnConvoPrompt(persona, all_utt, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


def run_gpt_prompt_memo_on_convo(persona, all_utt, test_input=None, verbose=False): 
  gpt_param = get_gpt_param({"max_tokens": 15, "stop": None})
  prompt = MemoOnConvoPrompt(persona, all_utt, verbose)
  return safe_execute_prompt(prompt, gpt_param, test_input)


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
