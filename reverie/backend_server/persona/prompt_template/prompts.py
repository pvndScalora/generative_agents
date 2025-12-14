import sys
import random
import string
import datetime
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *

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

class BasePrompt:
  """
  Abstract base class for GPT prompts.
  
  This class encapsulates the common logic for preparing, executing, and 
  validating GPT prompt requests. Subclasses should implement specific 
  logic for prompt construction, validation, and cleanup.
  """
  def __init__(self, persona, verbose=False):
    self.persona = persona
    self.verbose = verbose
    self.prompt_template = ""
    self.example_output = None
    self.special_instruction = None

  def create_prompt_input(self, test_input=None):
    """
    Creates the input list for the prompt template.
    Must be implemented by subclasses.
    """
    raise NotImplementedError

  def get_fail_safe(self):
    """
    Returns the fail-safe response in case of GPT failure.
    Must be implemented by subclasses.
    """
    raise NotImplementedError

  def validate(self, llm_response, prompt=""):
    """
    Validates the GPT response.
    Returns True if valid, False otherwise.
    """
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except: 
      return False

  def clean_up(self, llm_response, prompt=""):
    """
    Cleans up and parses the GPT response.
    Must be implemented by subclasses.
    """
    return llm_response



class WakeUpHourPrompt(BasePrompt):
  """
  Prompt to determine the hour when the persona wakes up.
  """
  def __init__(self, persona, verbose=False):
    super().__init__(persona, verbose)
    self.prompt_template = "persona/prompt_template/v2/wake_up_hour_v1.txt"

  def create_prompt_input(self, test_input=None):
    if test_input: return test_input
    prompt_input = [self.persona.scratch.get_str_iss(),
                    self.persona.scratch.get_str_lifestyle(),
                    self.persona.scratch.get_str_firstname()]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = int(llm_response.strip().lower().split("am")[0])
    return cr

  def get_fail_safe(self):
    return 8

class DailyPlanPrompt(BasePrompt):
  def __init__(self, persona, wake_up_hour, verbose=False):
    super().__init__(persona, verbose)
    self.wake_up_hour = wake_up_hour
    self.prompt_template = "persona/prompt_template/v2/daily_planning_v6.txt"

  def create_prompt_input(self, test_input=None):
    if test_input: return test_input
    prompt_input = []
    prompt_input += [self.persona.scratch.get_str_iss()]
    prompt_input += [self.persona.scratch.get_str_lifestyle()]
    prompt_input += [self.persona.scratch.get_str_curr_date_str()]
    prompt_input += [self.persona.scratch.get_str_firstname()]
    prompt_input += [f"{str(self.wake_up_hour)}:00 am"]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = []
    _cr = llm_response.split(")")
    for i in _cr: 
      if i[-1].isdigit(): 
        i = i[:-1].strip()
        if i[-1] == "." or i[-1] == ",": 
          cr += [i[:-1].strip()]
    return ([f"wake up and complete the morning routine at {self.wake_up_hour}:00 am"] + cr)

  def get_fail_safe(self):
    fs = ['wake up and complete the morning routine at 6:00 am', 
          'eat breakfast at 7:00 am', 
          'read a book from 8:00 am to 12:00 pm', 
          'have lunch at 12:00 pm', 
          'take a nap from 1:00 pm to 4:00 pm', 
          'relax and watch TV from 7:00 pm to 8:00 pm', 
          'go to bed at 11:00 pm'] 
    return fs

class HourlySchedulePrompt(BasePrompt):
  def __init__(self, persona, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2=None, verbose=False):
    super().__init__(persona, verbose)
    self.curr_hour_str = curr_hour_str
    self.p_f_ds_hourly_org = p_f_ds_hourly_org
    self.hour_str = hour_str
    self.intermission2 = intermission2
    self.prompt_template = "persona/prompt_template/v2/generate_hourly_schedule_v2.txt"

  def create_prompt_input(self, test_input=None):
    if test_input: return test_input
    schedule_format = ""
    for i in self.hour_str: 
      schedule_format += f"[{self.persona.scratch.get_str_curr_date_str()} -- {i}]"
      schedule_format += f" Activity: [Fill in]\n"
    schedule_format = schedule_format[:-1]

    intermission_str = f"Here the originally intended hourly breakdown of"
    intermission_str += f" {self.persona.scratch.get_str_firstname()}'s schedule today: "
    for count, i in enumerate(self.persona.scratch.daily_req): 
      intermission_str += f"{str(count+1)}) {i}, "
    intermission_str = intermission_str[:-2]

    prior_schedule = ""
    if self.p_f_ds_hourly_org: 
      prior_schedule = "\n"
      for count, i in enumerate(self.p_f_ds_hourly_org): 
        prior_schedule += f"[(ID:{get_random_alphanumeric()})" 
        prior_schedule += f" {self.persona.scratch.get_str_curr_date_str()} --"
        prior_schedule += f" {self.hour_str[count]}] Activity:"
        prior_schedule += f" {self.persona.scratch.get_str_firstname()}"
        prior_schedule += f" is {i}\n"

    prompt_ending = f"[(ID:{get_random_alphanumeric()})"
    prompt_ending += f" {self.persona.scratch.get_str_curr_date_str()}"
    prompt_ending += f" -- {self.curr_hour_str}] Activity:"
    prompt_ending += f" {self.persona.scratch.get_str_firstname()} is"

    if self.intermission2: 
      intermission2 = f"\n{self.intermission2}"

    prompt_input = []
    prompt_input += [schedule_format]
    prompt_input += [self.persona.scratch.get_str_iss()]

    prompt_input += [prior_schedule + "\n"]
    prompt_input += [intermission_str]
    if self.intermission2: 
      prompt_input += [intermission2]
    else: 
      prompt_input += [""]
    prompt_input += [prompt_ending]

    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = llm_response.strip()
    if cr[-1] == ".":
      cr = cr[:-1]
    return cr

  def get_fail_safe(self):
    return "asleep"

class TaskDecompPrompt(BasePrompt):
  def __init__(self, persona, task, duration, verbose=False):
    super().__init__(persona, verbose)
    self.task = task
    self.duration = duration
    self.prompt_template = "persona/prompt_template/v2/task_decomp_v3.txt"

  def create_prompt_input(self, test_input=None):
    curr_f_org_index = self.persona.scratch.get_f_daily_schedule_hourly_org_index()
    all_indices = []
    all_indices += [curr_f_org_index]
    if curr_f_org_index+1 <= len(self.persona.scratch.f_daily_schedule_hourly_org): 
      all_indices += [curr_f_org_index+1]
    if curr_f_org_index+2 <= len(self.persona.scratch.f_daily_schedule_hourly_org): 
      all_indices += [curr_f_org_index+2]

    curr_time_range = ""

    summ_str = f'Today is {self.persona.scratch.curr_time.strftime("%B %d, %Y")}. '
    summ_str += f'From '
    for index in all_indices: 
      if index < len(self.persona.scratch.f_daily_schedule_hourly_org): 
        start_min = 0
        for i in range(index): 
          start_min += self.persona.scratch.f_daily_schedule_hourly_org[i][1]
        end_min = start_min + self.persona.scratch.f_daily_schedule_hourly_org[index][1]
        start_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                      + datetime.timedelta(minutes=start_min)) 
        end_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S") 
                      + datetime.timedelta(minutes=end_min)) 
        start_time_str = start_time.strftime("%H:%M%p")
        end_time_str = end_time.strftime("%H:%M%p")
        summ_str += f"{start_time_str} ~ {end_time_str}, {self.persona.name} is planning on {self.persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
        if curr_f_org_index+1 == index:
          curr_time_range = f'{start_time_str} ~ {end_time_str}'
    summ_str = summ_str[:-2] + "."

    prompt_input = []
    prompt_input += [self.persona.scratch.get_str_iss()]
    prompt_input += [summ_str]
    prompt_input += [self.persona.scratch.get_str_firstname()]
    prompt_input += [self.persona.scratch.get_str_firstname()]
    prompt_input += [self.task]
    prompt_input += [curr_time_range]
    prompt_input += [self.duration]
    prompt_input += [self.persona.scratch.get_str_firstname()]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    temp = [i.strip() for i in llm_response.split("\n")]
    _cr = []
    cr = []
    for count, i in enumerate(temp): 
      if count != 0: 
        _cr += [" ".join([j.strip () for j in i.split(" ")][3:])]
      else: 
        _cr += [i]
    for count, i in enumerate(_cr): 
      k = [j.strip() for j in i.split("(duration in minutes:")]
      task = k[0]
      if task[-1] == ".": 
        task = task[:-1]
      duration = int(k[1].split(",")[0].strip())
      cr += [[task, duration]]

    total_expected_min = int(prompt.split("(total duration in minutes")[-1]
                                   .split("):")[0].strip())
    
    curr_min_slot = [["dummy", -1],] 
    for count, i in enumerate(cr): 
      i_task = i[0] 
      i_duration = i[1]

      i_duration -= (i_duration % 5)
      if i_duration > 0: 
        for j in range(i_duration): 
          curr_min_slot += [(i_task, count)]       
    curr_min_slot = curr_min_slot[1:]   

    if len(curr_min_slot) > total_expected_min: 
      last_task = curr_min_slot[60]
      for i in range(1, 6): 
        curr_min_slot[-1 * i] = last_task
    elif len(curr_min_slot) < total_expected_min: 
      last_task = curr_min_slot[-1]
      for i in range(total_expected_min - len(curr_min_slot)):
        curr_min_slot += [last_task]

    cr_ret = [["dummy", -1],]
    for task, task_index in curr_min_slot: 
      if task != cr_ret[-1][0]: 
        cr_ret += [[task, 1]]
      else: 
        cr_ret[-1][1] += 1
    cr = cr_ret[1:]

    output = cr
    fin_output = []
    time_sum = 0
    for i_task, i_duration in output: 
      time_sum += i_duration
      if time_sum <= self.duration: 
        fin_output += [[i_task, i_duration]]
      else: 
        break
    ftime_sum = 0
    for fi_task, fi_duration in fin_output: 
      ftime_sum += fi_duration
    
    if fin_output:
        fin_output[-1][1] += (self.duration - ftime_sum)
    output = fin_output 

    task_decomp = output
    ret = []
    for decomp_task, duration in task_decomp: 
      ret += [[f"{self.task} ({decomp_task})", duration]]
    output = ret

    return output

  def get_fail_safe(self):
    return ["asleep"]

class ActionSectorPrompt(BasePrompt):
  def __init__(self, persona, maze, action_description, verbose=False):
    super().__init__(persona, verbose)
    self.maze = maze
    self.action_description = action_description
    self.prompt_template = "persona/prompt_template/v1/action_location_sector_v1.txt"

  def create_prompt_input(self, test_input=None):
    act_world = f"{self.maze.access_tile(self.persona.scratch.curr_tile)['world']}"
    
    prompt_input = []
    
    prompt_input += [self.persona.scratch.get_str_name()]
    prompt_input += [self.persona.scratch.living_area.split(":")[1]]
    x = f"{act_world}:{self.persona.scratch.living_area.split(':')[1]}"
    prompt_input += [self.persona.s_mem.get_str_accessible_sector_arenas(x)]


    prompt_input += [self.persona.scratch.get_str_name()]
    prompt_input += [f"{self.maze.access_tile(self.persona.scratch.curr_tile)['sector']}"]
    x = f"{act_world}:{self.maze.access_tile(self.persona.scratch.curr_tile)['sector']}"
    prompt_input += [self.persona.s_mem.get_str_accessible_sector_arenas(x)]

    if self.persona.scratch.get_str_daily_plan_req() != "": 
      prompt_input += [f"\n{self.persona.scratch.get_str_daily_plan_req()}"]
    else: 
      prompt_input += [""]

    accessible_sector_str = self.persona.s_mem.get_str_accessible_sectors(act_world)
    curr = accessible_sector_str.split(", ")
    fin_accessible_sectors = []
    for i in curr: 
      if "'s house" in i: 
        if self.persona.scratch.last_name in i: 
          fin_accessible_sectors += [i]
      else: 
        fin_accessible_sectors += [i]
    accessible_sector_str = ", ".join(fin_accessible_sectors)

    prompt_input += [accessible_sector_str]

    action_description_1 = self.action_description
    action_description_2 = self.action_description
    if "(" in self.action_description: 
      action_description_1 = self.action_description.split("(")[0].strip()
      action_description_2 = self.action_description.split("(")[-1][:-1]
    prompt_input += [self.persona.scratch.get_str_name()]
    prompt_input += [action_description_1]

    prompt_input += [action_description_2]
    prompt_input += [self.persona.scratch.get_str_name()]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cleaned_response = llm_response.split("}")[0]
    y = f"{self.maze.access_tile(self.persona.scratch.curr_tile)['world']}"
    x = [i.strip() for i in self.persona.s_mem.get_str_accessible_sectors(y).split(",")]
    if cleaned_response not in x: 
      cleaned_response = self.persona.scratch.living_area.split(":")[1]
    return cleaned_response

  def validate(self, llm_response, prompt=""):
    if len(llm_response.strip()) < 1: 
      return False
    if "}" not in llm_response:
      return False
    if "," in llm_response: 
      return False
    return True

  def get_fail_safe(self):
    return "kitchen"

class ActionArenaPrompt(BasePrompt):
  def __init__(self, persona, maze, act_world, act_sector, action_description, verbose=False):
    super().__init__(persona, verbose)
    self.maze = maze
    self.act_world = act_world
    self.act_sector = act_sector
    self.action_description = action_description
    self.prompt_template = "persona/prompt_template/v1/action_location_object_vMar11.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = []
    prompt_input += [self.persona.scratch.get_str_name()]
    x = f"{self.act_world}:{self.act_sector}"
    prompt_input += [self.act_sector]

    accessible_arena_str = self.persona.s_mem.get_str_accessible_sector_arenas(x)
    curr = accessible_arena_str.split(", ")
    fin_accessible_arenas = []
    for i in curr: 
      if "'s room" in i: 
        if self.persona.scratch.last_name in i: 
          fin_accessible_arenas += [i]
      else: 
        fin_accessible_arenas += [i]
    accessible_arena_str = ", ".join(fin_accessible_arenas)

    prompt_input += [accessible_arena_str]

    action_description_1 = self.action_description
    action_description_2 = self.action_description
    if "(" in self.action_description: 
      action_description_1 = self.action_description.split("(")[0].strip()
      action_description_2 = self.action_description.split("(")[-1][:-1]
    prompt_input += [self.persona.scratch.get_str_name()]
    prompt_input += [action_description_1]

    prompt_input += [action_description_2]
    prompt_input += [self.persona.scratch.get_str_name()]
    prompt_input += [self.act_sector]
    prompt_input += [accessible_arena_str]
    
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cleaned_response = llm_response.split("}")[0]
    return cleaned_response

  def validate(self, llm_response, prompt=""):
    if len(llm_response.strip()) < 1: 
      return False
    if "}" not in llm_response:
      return False
    if "," in llm_response: 
      return False
    return True

  def get_fail_safe(self):
    return "kitchen"

class ActionGameObjectPrompt(BasePrompt):
  def __init__(self, persona, maze, temp_address, action_description, verbose=False):
    super().__init__(persona, verbose)
    self.maze = maze
    self.temp_address = temp_address
    self.action_description = action_description
    self.prompt_template = "persona/prompt_template/v1/action_object_v2.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = []
    action_description = self.action_description
    if "(" in action_description: 
      action_description = action_description.split("(")[-1][:-1]
      
    prompt_input += [action_description]
    prompt_input += [self.persona
                     .s_mem.get_str_accessible_arena_game_objects(self.temp_address)]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cleaned_response = llm_response.strip()
    x = [i.strip() for i in self.persona.s_mem.get_str_accessible_arena_game_objects(self.temp_address).split(",")]
    if cleaned_response not in x: 
      cleaned_response = random.choice(x)
    return cleaned_response

  def validate(self, llm_response, prompt=""):
    if len(llm_response.strip()) < 1: 
      return False
    return True

  def get_fail_safe(self):
    return "bed"

class PronunciatioPrompt(BasePrompt):
  def __init__(self, persona, action_description, verbose=False):
    super().__init__(persona, verbose)
    self.action_description = action_description
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/generate_pronunciatio_v1.txt"

  def create_prompt_input(self, test_input=None):
    action_description = self.action_description
    if "(" in action_description: 
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [action_description]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = llm_response.strip()
    if len(cr) > 3:
      cr = cr[:3]
    return cr

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt="")
      if len(llm_response) == 0: 
        return False
    except: return False
    return True 

  def get_fail_safe(self):
    return "😋"

class EventTriplePrompt(BasePrompt):
  def __init__(self, persona, action_description, verbose=False):
    super().__init__(persona, verbose)
    self.action_description = action_description
    self.prompt_template = "persona/prompt_template/v2/generate_event_triple_v1.txt"

  def create_prompt_input(self, test_input=None):
    action_description = self.action_description
    if "(" in action_description: 
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [self.persona.name, 
                    action_description,
                    self.persona.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = llm_response.strip()
    cr = [i.strip() for i in cr.split(")")[0].split(",")]
    return (self.persona.name, cr[0], cr[1])

  def validate(self, llm_response, prompt=""):
    try: 
      llm_response = self.clean_up(llm_response, prompt="")
      if len(llm_response) != 2: 
        return False
    except: return False
    return True 

  def get_fail_safe(self):
    return (self.persona.name, "is", "idle")

class ActObjDescPrompt(BasePrompt):
  def __init__(self, persona, act_game_object, act_desp, verbose=False):
    super().__init__(persona, verbose)
    self.act_game_object = act_game_object
    self.act_desp = act_desp
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/generate_obj_event_v1.txt"
    self.example_output = "being fixed"
    self.special_instruction = "The output should ONLY contain the phrase that should go in <fill in>."

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.act_game_object, 
                    self.persona.name,
                    self.act_desp,
                    self.act_game_object,
                    self.act_game_object]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = llm_response.strip()
    if cr[-1] == ".": cr = cr[:-1]
    return cr

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt="")
    except: 
      return False
    return True 

  def get_fail_safe(self):
    return f"{self.act_game_object} is idle"

class ActObjEventTriplePrompt(BasePrompt):
  def __init__(self, persona, act_game_object, act_obj_desc, verbose=False):
    super().__init__(persona, verbose)
    self.act_game_object = act_game_object
    self.act_obj_desc = act_obj_desc
    self.prompt_template = "persona/prompt_template/v2/generate_event_triple_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.act_game_object, 
                    self.act_obj_desc,
                    self.act_game_object]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    cr = llm_response.strip()
    cr = [i.strip() for i in cr.split(")")[0].split(",")]
    return (self.act_game_object, cr[0], cr[1])

  def validate(self, llm_response, prompt=""):
    try: 
      llm_response = self.clean_up(llm_response, prompt="")
      if len(llm_response) != 2: 
        return False
    except: return False
    return True 

  def get_fail_safe(self):
    return (self.act_game_object, "is", "idle")

class NewDecompSchedulePrompt(BasePrompt):
  def __init__(self, persona, main_act_dur, truncated_act_dur, start_time_hour, end_time_hour, inserted_act, inserted_act_dur, verbose=False):
    super().__init__(persona, verbose)
    self.main_act_dur = main_act_dur
    self.truncated_act_dur = truncated_act_dur
    self.start_time_hour = start_time_hour
    self.end_time_hour = end_time_hour
    self.inserted_act = inserted_act
    self.inserted_act_dur = inserted_act_dur
    self.prompt_template = "persona/prompt_template/v2/new_decomp_schedule_v1.txt"

  def create_prompt_input(self, test_input=None):
    persona_name = self.persona.name
    start_hour_str = self.start_time_hour.strftime("%H:%M %p")
    end_hour_str = self.end_time_hour.strftime("%H:%M %p")

    original_plan = ""
    for_time = self.start_time_hour
    for i in self.main_act_dur: 
      original_plan += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      original_plan += "\n"
      for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init = ""
    for_time = self.start_time_hour
    for count, i in enumerate(self.truncated_act_dur): 
      new_plan_init += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      new_plan_init += "\n"
      if count < len(self.truncated_act_dur) - 1: 
        for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M") + " ~"

    prompt_input = [persona_name, 
                    start_hour_str,
                    end_hour_str,
                    original_plan,
                    persona_name,
                    self.inserted_act,
                    self.inserted_act_dur,
                    persona_name,
                    start_hour_str,
                    end_hour_str,
                    end_hour_str,
                    new_plan_init]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    new_schedule = prompt + " " + llm_response.strip()
    new_schedule = new_schedule.split("The revised schedule:")[-1].strip()
    new_schedule = new_schedule.split("\n")

    ret_temp = []
    for i in new_schedule: 
      ret_temp += [i.split(" -- ")]

    ret = []
    for time_str, action in ret_temp:
      start_time = time_str.split(" ~ ")[0].strip()
      end_time = time_str.split(" ~ ")[1].strip()
      delta = datetime.datetime.strptime(end_time, "%H:%M") - datetime.datetime.strptime(start_time, "%H:%M")
      delta_min = int(delta.total_seconds()/60)
      if delta_min < 0: delta_min = 0
      ret += [[action, delta_min]]

    return ret

  def validate(self, llm_response, prompt=""):
    try: 
      llm_response = self.clean_up(llm_response, prompt)
      dur_sum = 0
      for act, dur in llm_response: 
        dur_sum += dur
        if str(type(act)) != "<class 'str'>":
          return False 
        if str(type(dur)) != "<class 'int'>":
          return False
      
      x = prompt.split("\n")[0].split("originally planned schedule from")[-1].strip()[:-1]
      x = [datetime.datetime.strptime(i.strip(), "%H:%M %p") for i in x.split(" to ")]
      delta_min = int((x[1] - x[0]).total_seconds()/60)

      if int(dur_sum) != int(delta_min): 
        return False

    except: 
      return False
    return True 

  def get_fail_safe(self):
    dur_sum = 0
    for act, dur in self.main_act_dur: dur_sum += dur

    ret = self.truncated_act_dur[:]
    ret += self.main_act_dur[len(ret)-1:]

    ret_dur_sum = 0
    count = 0
    over = None
    for act, dur in ret: 
      ret_dur_sum += dur
      if ret_dur_sum == dur_sum: 
        break
      if ret_dur_sum > dur_sum: 
        over = ret_dur_sum - dur_sum
        break
      count += 1 

    if over: 
      ret = ret[:count+1]
      ret[-1][1] -= over

    return ret

class DecideToTalkPrompt(BasePrompt):
  def __init__(self, persona, target_persona, retrieved, verbose=False):
    super().__init__(persona, verbose)
    self.target_persona = target_persona
    self.retrieved = retrieved
    self.prompt_template = "persona/prompt_template/v2/decide_to_talk_v2.txt"

  def create_prompt_input(self, test_input=None):
    last_chat = self.persona.a_mem.get_last_chat(self.target_persona.name)
    last_chatted_time = ""
    last_chat_about = ""
    if last_chat: 
      last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
      last_chat_about = last_chat.description

    context = ""
    for c_node in self.retrieved["events"]: 
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context +=  f"{curr_desc}. "
    context += "\n"
    for c_node in self.retrieved["thoughts"]: 
      context +=  f"{c_node.description}. "

    curr_time = self.persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_act_desc = self.persona.scratch.act_description
    if "(" in init_act_desc: 
      init_act_desc = init_act_desc.split("(")[-1][:-1]
    
    if len(self.persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc: 
      init_p_desc = f"{self.persona.name} is already {init_act_desc}"
    elif "waiting" in init_act_desc:
      init_p_desc = f"{self.persona.name} is {init_act_desc}"
    else: 
      init_p_desc = f"{self.persona.name} is on the way to {init_act_desc}"

    target_act_desc = self.target_persona.scratch.act_description
    if "(" in target_act_desc: 
      target_act_desc = target_act_desc.split("(")[-1][:-1]
    
    if len(self.target_persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc: 
      target_p_desc = f"{self.target_persona.name} is already {target_act_desc}"
    elif "waiting" in init_act_desc:
      target_p_desc = f"{self.persona.name} is {init_act_desc}"
    else: 
      target_p_desc = f"{self.target_persona.name} is on the way to {target_act_desc}"


    prompt_input = []
    prompt_input += [context]

    prompt_input += [curr_time]

    prompt_input += [self.persona.name]
    prompt_input += [self.target_persona.name]
    prompt_input += [last_chatted_time]
    prompt_input += [last_chat_about]


    prompt_input += [init_p_desc]
    prompt_input += [target_p_desc]
    prompt_input += [self.persona.name]
    prompt_input += [self.target_persona.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split("Answer in yes or no:")[-1].strip().lower()

  def validate(self, llm_response, prompt=""):
    try: 
      if llm_response.split("Answer in yes or no:")[-1].strip().lower() in ["yes", "no"]: 
        return True
      return False     
    except:
      return False 

  def get_fail_safe(self):
    return "yes"

class DecideToReactPrompt(BasePrompt):
  def __init__(self, persona, target_persona, retrieved, verbose=False):
    super().__init__(persona, verbose)
    self.target_persona = target_persona
    self.retrieved = retrieved
    self.prompt_template = "persona/prompt_template/v2/decide_to_react_v1.txt"

  def create_prompt_input(self, test_input=None):
    context = ""
    for c_node in self.retrieved["events"]: 
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context +=  f"{curr_desc}. "
    context += "\n"
    for c_node in self.retrieved["thoughts"]: 
      context +=  f"{c_node.description}. "

    curr_time = self.persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_act_desc = self.persona.scratch.act_description
    if "(" in init_act_desc: 
      init_act_desc = init_act_desc.split("(")[-1][:-1]
    if len(self.persona.scratch.planned_path) == 0: 
      loc = ""
      if ":" in self.persona.scratch.act_address:
        loc = self.persona.scratch.act_address.split(":")[-1] + " in " + self.persona.scratch.act_address.split(":")[-2]
      init_p_desc = f"{self.persona.name} is already {init_act_desc} at {loc}"
    else: 
      loc = ""
      if ":" in self.persona.scratch.act_address:
        loc = self.persona.scratch.act_address.split(":")[-1] + " in " + self.persona.scratch.act_address.split(":")[-2]
      init_p_desc = f"{self.persona.name} is on the way to {init_act_desc} at {loc}"

    target_act_desc = self.target_persona.scratch.act_description
    if "(" in target_act_desc: 
      target_act_desc = target_act_desc.split("(")[-1][:-1]
    if len(self.target_persona.scratch.planned_path) == 0: 
      loc = ""
      if ":" in self.target_persona.scratch.act_address:
        loc = self.target_persona.scratch.act_address.split(":")[-1] + " in " + self.target_persona.scratch.act_address.split(":")[-2]
      target_p_desc = f"{self.target_persona.name} is already {target_act_desc} at {loc}"
    else: 
      loc = ""
      if ":" in self.target_persona.scratch.act_address:
        loc = self.target_persona.scratch.act_address.split(":")[-1] + " in " + self.target_persona.scratch.act_address.split(":")[-2]
      target_p_desc = f"{self.target_persona.name} is on the way to {target_act_desc} at {loc}"

    prompt_input = []
    prompt_input += [context]
    prompt_input += [curr_time]
    prompt_input += [init_p_desc]
    prompt_input += [target_p_desc]

    prompt_input += [self.persona.name]
    prompt_input += [init_act_desc]
    prompt_input += [self.target_persona.name]
    prompt_input += [target_act_desc]

    prompt_input += [init_act_desc]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split("Answer: Option")[-1].strip().lower()

  def validate(self, llm_response, prompt=""):
    try: 
      if llm_response.split("Answer: Option")[-1].strip().lower() in ["1", "2", "3"]: 
        return True
      return False     
    except:
      return False 

  def get_fail_safe(self):
    return "3"

class CreateConversationPrompt(BasePrompt):
  def __init__(self, persona, target_persona, curr_loc, verbose=False):
    super().__init__(persona, verbose)
    self.target_persona = target_persona
    self.curr_loc = curr_loc
    self.prompt_template = "persona/prompt_template/v2/create_conversation_v2.txt"

  def create_prompt_input(self, test_input=None):
    prev_convo_insert = "\n"
    if self.persona.a_mem.seq_chat: 
      for i in self.persona.a_mem.seq_chat: 
        if i.object == self.target_persona.scratch.name: 
          v1 = int((self.persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, {self.persona.scratch.name} and {self.target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if self.persona.a_mem.seq_chat: 
      if int((self.persona.scratch.curr_time - self.persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""

    prompt_input = [self.persona.scratch.get_str_curr_date_str(),
                    self.curr_loc, 
                    prev_convo_insert,
                    self.persona.scratch.get_str_name(),
                    self.target_persona.scratch.get_str_name(),
                    self.persona.scratch.get_str_iss(),
                    self.target_persona.scratch.get_str_iss(),
                    self.persona.scratch.get_str_name(),
                    self.target_persona.scratch.get_str_name(),
                    self.persona.scratch.get_str_name(),
                    self.target_persona.scratch.get_str_name()]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = (prompt + llm_response).split("Here is their conversation.")[-1].strip()
    content = re.findall('"([^"]*)"', llm_response)

    speaker_order = []
    for i in llm_response.split("\n"): 
      name = i.split(":")[0].strip() 
      if name: 
        speaker_order += [name]

    ret = []
    for count, speaker in enumerate(speaker_order): 
      ret += [[speaker, content[count]]]

    return ret

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class SummarizeConversationPrompt(BasePrompt):
  def __init__(self, persona, conversation, verbose=False):
    super().__init__(persona, verbose)
    self.conversation = conversation
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/summarize_conversation_v1.txt"
    self.example_output = "conversing about what to eat for lunch"
    self.special_instruction = "The output must continue the sentence above by filling in the <fill in> tag. Don't start with 'this is a conversation about...' Just finish the sentence but do not miss any important details (including who are chatting)."

  def create_prompt_input(self, test_input=None):
    convo_str = ""
    for row in self.conversation: 
      convo_str += f'{row[0]}: "{row[1]}"\n'

    prompt_input = [convo_str]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    ret = "conversing about " + llm_response.strip()
    return ret

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "conversing with a housemate about morning greetings"

class ExtractKeywordsPrompt(BasePrompt):
  def __init__(self, persona, description, verbose=False):
    super().__init__(persona, verbose)
    self.description = description
    self.prompt_template = "persona/prompt_template/v2/get_keywords_v1.txt"

  def create_prompt_input(self, test_input=None):
    description = self.description
    if "\n" in description: 
      description = description.replace("\n", " <LINE_BREAK> ")
    prompt_input = [description]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = llm_response.strip().split("Emotive keywords:")
    factual = [i.strip() for i in llm_response[0].split(",")]
    emotive = [i.strip() for i in llm_response[1].split(",")]
    all_keywords = factual + emotive
    ret = []
    for i in all_keywords: 
      if i: 
        i = i.lower()
        if i[-1] == ".": 
          i = i[:-1]
        ret += [i]
    return set(ret)

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return []

class KeywordToThoughtsPrompt(BasePrompt):
  def __init__(self, persona, keyword, concept_summary, verbose=False):
    super().__init__(persona, verbose)
    self.keyword = keyword
    self.concept_summary = concept_summary
    self.prompt_template = "persona/prompt_template/v2/keyword_to_thoughts_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.keyword, self.concept_summary, self.persona.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = llm_response.strip()
    return llm_response

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return ""

class ConvoToThoughtsPrompt(BasePrompt):
  def __init__(self, persona, init_persona_name, target_persona_name, convo_str, fin_target, verbose=False):
    super().__init__(persona, verbose)
    self.init_persona_name = init_persona_name
    self.target_persona_name = target_persona_name
    self.convo_str = convo_str
    self.fin_target = fin_target
    self.prompt_template = "persona/prompt_template/v2/convo_to_thoughts_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.init_persona_name,
                    self.target_persona_name,
                    self.convo_str,
                    self.init_persona_name,
                    self.fin_target]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = llm_response.strip()
    return llm_response

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return ""

class EventPoignancyPrompt(BasePrompt):
  def __init__(self, persona, event_description, verbose=False):
    super().__init__(persona, verbose)
    self.event_description = event_description
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/poignancy_event_v1.txt"
    self.example_output = "5"
    self.special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.name,
                    self.persona.scratch.get_str_iss(),
                    self.persona.scratch.name,
                    self.event_description]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = int(llm_response.strip())
    return llm_response

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return 4

class ThoughtPoignancyPrompt(BasePrompt):
  def __init__(self, persona, event_description, verbose=False):
    super().__init__(persona, verbose)
    self.event_description = event_description
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/poignancy_thought_v1.txt"
    self.example_output = "5"
    self.special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.name,
                    self.persona.scratch.get_str_iss(),
                    self.persona.scratch.name,
                    self.event_description]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = int(llm_response.strip())
    return llm_response

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return 4

class ChatPoignancyPrompt(BasePrompt):
  def __init__(self, persona, event_description, verbose=False):
    super().__init__(persona, verbose)
    self.event_description = event_description
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/poignancy_chat_v1.txt"
    self.example_output = "5"
    self.special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.name,
                    self.persona.scratch.get_str_iss(),
                    self.persona.scratch.name,
                    self.event_description]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = int(llm_response.strip())
    return llm_response

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return 4

class FocalPtPrompt(BasePrompt):
  def __init__(self, persona, statements, n, verbose=False):
    super().__init__(persona, verbose)
    self.statements = statements
    self.n = n
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/generate_focal_pt_v1.txt"
    self.example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
    self.special_instruction = "Output must be a list of str."

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.statements, str(self.n)]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    ret = ast.literal_eval(llm_response)
    return ret

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return ["Who am I"] * self.n

class InsightAndGuidancePrompt(BasePrompt):
  def __init__(self, persona, statements, n, verbose=False):
    super().__init__(persona, verbose)
    self.statements = statements
    self.n = n
    self.prompt_template = "persona/prompt_template/v2/insight_and_evidence_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.statements, str(self.n)]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = "1. " + llm_response.strip()
    ret = dict()
    for i in llm_response.split("\n"): 
      row = i.split(". ")[-1]
      thought = row.split("(because of ")[0].strip()
      evi_raw = row.split("(because of ")[1].split(")")[0].strip()
      evi_raw = re.findall(r'\d+', evi_raw)
      evi_raw = [int(i.strip()) for i in evi_raw]
      ret[thought] = evi_raw
    return ret

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return ["I am hungry"] * self.n

class AgentChatSummarizeIdeasPrompt(BasePrompt):
  def __init__(self, persona, target_persona, statements, curr_context, verbose=False):
    super().__init__(persona, verbose)
    self.target_persona = target_persona
    self.statements = statements
    self.curr_context = curr_context
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/summarize_chat_ideas_v1.txt"
    self.example_output = 'Jane Doe is working on a project'
    self.special_instruction = 'The output should be a string that responds to the question.'

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.get_str_curr_date_str(), self.curr_context, self.persona.scratch.currently, 
                    self.statements, self.persona.scratch.name, self.target_persona.scratch.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class AgentChatSummarizeRelationshipPrompt(BasePrompt):
  def __init__(self, persona, target_persona, statements, verbose=False):
    super().__init__(persona, verbose)
    self.target_persona = target_persona
    self.statements = statements
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/summarize_chat_relationship_v2.txt"
    self.example_output = 'Jane Doe is working on a project'
    self.special_instruction = 'The output should be a string that responds to the question.'

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.statements, self.persona.scratch.name, self.target_persona.scratch.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class AgentChatPrompt(BasePrompt):
  def __init__(self, persona, maze, target_persona, curr_context, init_summ_idea, target_summ_idea, verbose=False):
    super().__init__(persona, verbose)
    self.maze = maze
    self.target_persona = target_persona
    self.curr_context = curr_context
    self.init_summ_idea = init_summ_idea
    self.target_summ_idea = target_summ_idea
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/agent_chat_v1.txt"
    self.example_output = '[["Jane Doe", "Hi!"], ["John Doe", "Hello there!"] ... ]'
    self.special_instruction = 'The output should be a list of list where the inner lists are in the form of ["<Name>", "<Utterance>"].'

  def create_prompt_input(self, test_input=None):
    prev_convo_insert = "\n"
    if self.persona.a_mem.seq_chat: 
      for i in self.persona.a_mem.seq_chat: 
        if i.object == self.target_persona.scratch.name: 
          v1 = int((self.persona.scratch.curr_time - i.created).total_seconds()/60)
          prev_convo_insert += f'{str(v1)} minutes ago, {self.persona.scratch.name} and {self.target_persona.scratch.name} were already {i.description} This context takes place after that conversation.'
          break
    if prev_convo_insert == "\n": 
      prev_convo_insert = ""
    if self.persona.a_mem.seq_chat: 
      if int((self.persona.scratch.curr_time - self.persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
        prev_convo_insert = ""

    curr_sector = f"{self.maze.access_tile(self.persona.scratch.curr_tile)['sector']}"
    curr_arena= f"{self.maze.access_tile(self.persona.scratch.curr_tile)['arena']}"
    curr_location = f"{curr_arena} in {curr_sector}"
    

    prompt_input = [self.persona.scratch.currently, 
                    self.target_persona.scratch.currently, 
                    prev_convo_insert,
                    self.curr_context, 
                    curr_location,

                    self.persona.scratch.name,
                    self.init_summ_idea, 
                    self.persona.scratch.name,
                    self.target_persona.scratch.name,

                    self.target_persona.scratch.name,
                    self.target_summ_idea, 
                    self.target_persona.scratch.name,
                    self.persona.scratch.name,

                    self.persona.scratch.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    llm_response = (prompt + llm_response).split("Here is their conversation.")[-1].strip()
    content = re.findall('"([^"]*)"', llm_response)

    speaker_order = []
    for i in llm_response.split("\n"): 
      name = i.split(":")[0].strip() 
      if name: 
        speaker_order += [name]

    ret = []
    for count, speaker in enumerate(speaker_order): 
      ret += [[speaker, content[count]]]

    return ret

  def validate(self, llm_response, prompt=""):
    return True

  def get_fail_safe(self):
    return "..."

class SummarizeIdeasPrompt(BasePrompt):
  def __init__(self, persona, statements, question, verbose=False):
    super().__init__(persona, verbose)
    self.statements = statements
    self.question = question
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/summarize_ideas_v1.txt"
    self.example_output = 'Jane Doe is working on a project'
    self.special_instruction = 'The output should be a string that responds to the question.'

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.statements, self.persona.scratch.name, self.question]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class GenerateNextConvoLinePrompt(BasePrompt):
  def __init__(self, persona, interlocutor_desc, prev_convo, retrieved_summary, verbose=False):
    super().__init__(persona, verbose)
    self.interlocutor_desc = interlocutor_desc
    self.prev_convo = prev_convo
    self.retrieved_summary = retrieved_summary
    self.prompt_template = "persona/prompt_template/v2/generate_next_convo_line_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.name, 
                    self.persona.scratch.get_str_iss(),
                    self.persona.scratch.name, 
                    self.interlocutor_desc, 
                    self.prev_convo, 
                    self.persona.scratch.name,
                    self.retrieved_summary, 
                    self.persona.scratch.name,]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class WhisperInnerThoughtPrompt(BasePrompt):
  def __init__(self, persona, whisper, verbose=False):
    super().__init__(persona, verbose)
    self.whisper = whisper
    self.prompt_template = "persona/prompt_template/v2/whisper_inner_thought_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.persona.scratch.name, self.whisper]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class PlanningThoughtOnConvoPrompt(BasePrompt):
  def __init__(self, persona, all_utt, verbose=False):
    super().__init__(persona, verbose)
    self.all_utt = all_utt
    self.prompt_template = "persona/prompt_template/v2/planning_thought_on_convo_v1.txt"

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.all_utt, self.persona.scratch.name, self.persona.scratch.name, self.persona.scratch.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.split('"')[0].strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."

class MemoOnConvoPrompt(BasePrompt):
  def __init__(self, persona, all_utt, verbose=False):
    super().__init__(persona, verbose)
    self.all_utt = all_utt
    self.prompt_template = "persona/prompt_template/v3_ChatGPT/memo_on_convo_v1.txt"
    self.example_output = 'Jane Doe was interesting to talk to.'
    self.special_instruction = 'The output should ONLY contain a string that summarizes anything interesting that the agent may have noticed'

  def create_prompt_input(self, test_input=None):
    prompt_input = [self.all_utt, self.persona.scratch.name, self.persona.scratch.name, self.persona.scratch.name]
    return prompt_input

  def clean_up(self, llm_response, prompt=""):
    return llm_response.strip()

  def validate(self, llm_response, prompt=""):
    try: 
      self.clean_up(llm_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(self):
    return "..."
