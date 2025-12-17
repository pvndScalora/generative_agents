"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: scratch.py
Description: Defines the short-term memory module for generative agents.
"""
import datetime
import json
import sys
sys.path.append('../../')

from reverie.backend_server.models import PersonaIdentity, CognitiveParams, CurrentAction, Coordinate, Action
from global_methods import check_if_file_exists
from .state import PersonaState, IdentityProfile, WorldContext, ExecutiveState, ActionState, SocialContext

class Scratch: 
  def __init__(self, scratch_load): 
    # Initialize Data Models
    identity = PersonaIdentity(
        name="Placeholder Name", 
        age=0,
        innate="", learned="", currently="", lifestyle="", living_area=""
    )
    cognitive_params = CognitiveParams()

    self.state = PersonaState(
        identity_profile=IdentityProfile(identity, cognitive_params),
        world_context=WorldContext(),
        executive_state=ExecutiveState(),
        action_state=ActionState(),
        social_context=SocialContext()
    )

    if scratch_load: 
      self.state.identity_profile.cognitive_params.vision_r = scratch_load["vision_r"]
      self.state.identity_profile.cognitive_params.att_bandwidth = scratch_load["att_bandwidth"]
      self.state.identity_profile.cognitive_params.retention = scratch_load["retention"]

      if scratch_load["curr_time"]: 
        self.state.world_context.curr_time = datetime.datetime.strptime(scratch_load["curr_time"],
                                                  "%B %d, %Y, %H:%M:%S")
      else: 
        self.state.world_context.curr_time = None
      if scratch_load["curr_tile"]:
        self.state.world_context.curr_tile = Coordinate(*scratch_load["curr_tile"])
      else:
        self.state.world_context.curr_tile = None
      self.state.executive_state.daily_plan_req = scratch_load["daily_plan_req"]

      self.state.identity_profile.identity.name = scratch_load["name"]
      self.state.identity_profile.identity.age = scratch_load["age"]
      self.state.identity_profile.identity.innate = scratch_load["innate"]
      self.state.identity_profile.identity.learned = scratch_load["learned"]
      self.state.identity_profile.identity.currently = scratch_load["currently"]
      self.state.identity_profile.identity.lifestyle = scratch_load["lifestyle"]
      self.state.identity_profile.identity.living_area = scratch_load["living_area"]

      self.state.identity_profile.cognitive_params.concept_forget = scratch_load["concept_forget"]
      self.state.identity_profile.cognitive_params.daily_reflection_time = scratch_load["daily_reflection_time"]
      self.state.identity_profile.cognitive_params.daily_reflection_size = scratch_load["daily_reflection_size"]
      self.state.identity_profile.cognitive_params.overlap_reflect_th = scratch_load["overlap_reflect_th"]
      self.state.identity_profile.cognitive_params.kw_strg_event_reflect_th = scratch_load["kw_strg_event_reflect_th"]
      self.state.identity_profile.cognitive_params.kw_strg_thought_reflect_th = scratch_load["kw_strg_thought_reflect_th"]

      self.state.identity_profile.cognitive_params.recency_weight = scratch_load["recency_w"]
      self.state.identity_profile.cognitive_params.relevance_weight = scratch_load["relevance_w"]
      self.state.identity_profile.cognitive_params.importance_weight = scratch_load["importance_w"]
      self.state.identity_profile.cognitive_params.recency_decay = scratch_load["recency_decay"]
      self.state.identity_profile.cognitive_params.importance_trigger_max = scratch_load["importance_trigger_max"]
      self.state.identity_profile.cognitive_params.importance_trigger_curr = scratch_load["importance_trigger_curr"]
      self.state.identity_profile.cognitive_params.importance_ele_n = scratch_load["importance_ele_n"]
      self.state.identity_profile.cognitive_params.thought_count = scratch_load.get("thought_count", 5)

      self.state.executive_state.daily_req = scratch_load["daily_req"]
      self.state.executive_state.f_daily_schedule = [Action(description=x[0], duration=x[1]) for x in scratch_load["f_daily_schedule"]]
      self.state.executive_state.f_daily_schedule_hourly_org = [Action(description=x[0], duration=x[1]) for x in scratch_load["f_daily_schedule_hourly_org"]]

      self.state.action_state.current_action.address = scratch_load["act_address"]
      if scratch_load["act_start_time"]: 
        self.state.action_state.current_action.start_time = datetime.datetime.strptime(
                                              scratch_load["act_start_time"],
                                              "%B %d, %Y, %H:%M:%S")
      else: 
        self.state.action_state.current_action.start_time = None 
      
      self.state.action_state.current_action.duration = scratch_load["act_duration"]
      self.state.action_state.current_action.description = scratch_load["act_description"]
      self.state.action_state.current_action.pronunciatio = scratch_load["act_pronunciatio"]
      self.state.action_state.current_action.event = tuple(scratch_load["act_event"])

      self.state.action_state.current_action.obj_description = scratch_load["act_obj_description"]
      self.state.action_state.current_action.obj_pronunciatio = scratch_load["act_obj_pronunciatio"]
      self.state.action_state.current_action.obj_event = tuple(scratch_load["act_obj_event"])

      self.state.social_context.chatting_with = scratch_load["chatting_with"]
      self.state.social_context.chat = scratch_load["chat"]
      self.state.social_context.chatting_with_buffer = scratch_load["chatting_with_buffer"]
      if scratch_load["chatting_end_time"]: 
        self.state.social_context.chatting_end_time = datetime.datetime.strptime(
                                            scratch_load["chatting_end_time"],
                                            "%B %d, %Y, %H:%M:%S")
      else:
        self.state.social_context.chatting_end_time = None

      self.state.action_state.act_path_set = scratch_load["act_path_set"]
      self.state.action_state.planned_path = [Coordinate(*p) for p in scratch_load["planned_path"]]

  @property
  def scratch(self):
      """
      Helper property to allow this object to be passed where 'persona.scratch' is expected.
      This aids in refactoring by allowing Scratch to mimic the Persona structure for prompts.
      """
      return self

  # PROPERTIES FOR BACKWARD COMPATIBILITY
  @property
  def identity(self): return self.state.identity_profile.identity
  
  @property
  def cognitive_params(self): return self.state.identity_profile.cognitive_params

  @property
  def curr_time(self): return self.state.world_context.curr_time
  @curr_time.setter
  def curr_time(self, value): self.state.world_context.curr_time = value

  @property
  def curr_tile(self): return self.state.world_context.curr_tile
  @curr_tile.setter
  def curr_tile(self, value): self.state.world_context.curr_tile = value

  @property
  def daily_plan_req(self): return self.state.executive_state.daily_plan_req
  @daily_plan_req.setter
  def daily_plan_req(self, value): self.state.executive_state.daily_plan_req = value

  @property
  def daily_req(self): return self.state.executive_state.daily_req
  @daily_req.setter
  def daily_req(self, value): self.state.executive_state.daily_req = value

  @property
  def f_daily_schedule(self): return self.state.executive_state.f_daily_schedule
  @f_daily_schedule.setter
  def f_daily_schedule(self, value): self.state.executive_state.f_daily_schedule = value

  @property
  def f_daily_schedule_hourly_org(self): return self.state.executive_state.f_daily_schedule_hourly_org
  @f_daily_schedule_hourly_org.setter
  def f_daily_schedule_hourly_org(self, value): self.state.executive_state.f_daily_schedule_hourly_org = value

  @property
  def act(self): return self.state.action_state.current_action
  @act.setter
  def act(self, value): self.state.action_state.current_action = value

  @property
  def chatting_with(self): return self.state.social_context.chatting_with
  @chatting_with.setter
  def chatting_with(self, value): self.state.social_context.chatting_with = value

  @property
  def chat(self): return self.state.social_context.chat
  @chat.setter
  def chat(self, value): self.state.social_context.chat = value

  @property
  def chatting_with_buffer(self): return self.state.social_context.chatting_with_buffer
  @chatting_with_buffer.setter
  def chatting_with_buffer(self, value): self.state.social_context.chatting_with_buffer = value

  @property
  def chatting_end_time(self): return self.state.social_context.chatting_end_time
  @chatting_end_time.setter
  def chatting_end_time(self, value): self.state.social_context.chatting_end_time = value

  @property
  def act_path_set(self): return self.state.action_state.act_path_set
  @act_path_set.setter
  def act_path_set(self, value): self.state.action_state.act_path_set = value

  @property
  def planned_path(self): return self.state.action_state.planned_path
  @planned_path.setter
  def planned_path(self, value): self.state.action_state.planned_path = value

  @property
  def a_mem(self): return self.state.memory_system.associative_memory

  @property
  def s_mem(self): return self.state.memory_system.spatial_memory

  @property
  def vision_r(self): return self.cognitive_params.vision_r
  @vision_r.setter
  def vision_r(self, value): self.cognitive_params.vision_r = value

  @property
  def att_bandwidth(self): return self.cognitive_params.att_bandwidth
  @att_bandwidth.setter
  def att_bandwidth(self, value): self.cognitive_params.att_bandwidth = value

  @property
  def retention(self): return self.cognitive_params.retention
  @retention.setter
  def retention(self, value): self.cognitive_params.retention = value

  @property
  def name(self): return self.identity.name
  @name.setter
  def name(self, value): self.identity.name = value

  @property
  def first_name(self): return self.identity.name.split(" ")[0] if self.identity.name else ""
  @first_name.setter
  def first_name(self, value): pass 

  @property
  def last_name(self): return self.identity.name.split(" ")[-1] if self.identity.name else ""
  @last_name.setter
  def last_name(self, value): pass 

  @property
  def age(self): return self.identity.age
  @age.setter
  def age(self, value): self.identity.age = value

  @property
  def innate(self): return self.identity.innate
  @innate.setter
  def innate(self, value): self.identity.innate = value

  @property
  def learned(self): return self.identity.learned
  @learned.setter
  def learned(self, value): self.identity.learned = value

  @property
  def currently(self): return self.identity.currently
  @currently.setter
  def currently(self, value): self.identity.currently = value

  @property
  def lifestyle(self): return self.identity.lifestyle
  @lifestyle.setter
  def lifestyle(self, value): self.identity.lifestyle = value

  @property
  def living_area(self): return self.identity.living_area
  @living_area.setter
  def living_area(self, value): self.identity.living_area = value

  @property
  def concept_forget(self): return self.cognitive_params.concept_forget
  @concept_forget.setter
  def concept_forget(self, value): self.cognitive_params.concept_forget = value

  @property
  def daily_reflection_time(self): return self.cognitive_params.daily_reflection_time
  @daily_reflection_time.setter
  def daily_reflection_time(self, value): self.cognitive_params.daily_reflection_time = value

  @property
  def daily_reflection_size(self): return self.cognitive_params.daily_reflection_size
  @daily_reflection_size.setter
  def daily_reflection_size(self, value): self.cognitive_params.daily_reflection_size = value

  @property
  def overlap_reflect_th(self): return self.cognitive_params.overlap_reflect_th
  @overlap_reflect_th.setter
  def overlap_reflect_th(self, value): self.cognitive_params.overlap_reflect_th = value

  @property
  def kw_strg_event_reflect_th(self): return self.cognitive_params.kw_strg_event_reflect_th
  @kw_strg_event_reflect_th.setter
  def kw_strg_event_reflect_th(self, value): self.cognitive_params.kw_strg_event_reflect_th = value

  @property
  def kw_strg_thought_reflect_th(self): return self.cognitive_params.kw_strg_thought_reflect_th
  @kw_strg_thought_reflect_th.setter
  def kw_strg_thought_reflect_th(self, value): self.cognitive_params.kw_strg_thought_reflect_th = value

  @property
  def recency_w(self): return self.cognitive_params.recency_weight
  @recency_w.setter
  def recency_w(self, value): self.cognitive_params.recency_weight = value

  @property
  def relevance_w(self): return self.cognitive_params.relevance_weight
  @relevance_w.setter
  def relevance_w(self, value): self.cognitive_params.relevance_weight = value

  @property
  def importance_w(self): return self.cognitive_params.importance_weight
  @importance_w.setter
  def importance_w(self, value): self.cognitive_params.importance_weight = value

  @property
  def recency_decay(self): return self.cognitive_params.recency_decay
  @recency_decay.setter
  def recency_decay(self, value): self.cognitive_params.recency_decay = value

  @property
  def importance_trigger_max(self): return self.cognitive_params.importance_trigger_max
  @importance_trigger_max.setter
  def importance_trigger_max(self, value): self.cognitive_params.importance_trigger_max = value

  @property
  def importance_trigger_curr(self): return self.cognitive_params.importance_trigger_curr
  @importance_trigger_curr.setter
  def importance_trigger_curr(self, value): self.cognitive_params.importance_trigger_curr = value

  @property
  def importance_ele_n(self): return self.cognitive_params.importance_ele_n
  @importance_ele_n.setter
  def importance_ele_n(self, value): self.cognitive_params.importance_ele_n = value

  @property
  def thought_count(self): return self.cognitive_params.thought_count
  @thought_count.setter
  def thought_count(self, value): self.cognitive_params.thought_count = value

  @property
  def act_address(self): return self.act.address
  @act_address.setter
  def act_address(self, value): self.act.address = value

  @property
  def act_start_time(self): return self.act.start_time
  @act_start_time.setter
  def act_start_time(self, value): self.act.start_time = value

  @property
  def act_duration(self): return self.act.duration
  @act_duration.setter
  def act_duration(self, value): self.act.duration = value

  @property
  def act_description(self): return self.act.description
  @act_description.setter
  def act_description(self, value): self.act.description = value

  @property
  def act_pronunciatio(self): return self.act.pronunciatio
  @act_pronunciatio.setter
  def act_pronunciatio(self, value): self.act.pronunciatio = value

  @property
  def act_event(self): return self.act.event
  @act_event.setter
  def act_event(self, value): self.act.event = value

  @property
  def act_obj_description(self): return self.act.obj_description
  @act_obj_description.setter
  def act_obj_description(self, value): self.act.obj_description = value

  @property
  def act_obj_pronunciatio(self): return self.act.obj_pronunciatio
  @act_obj_pronunciatio.setter
  def act_obj_pronunciatio(self, value): self.act.obj_pronunciatio = value

  @property
  def act_obj_event(self): return self.act.obj_event
  @act_obj_event.setter
  def act_obj_event(self, value): self.act.obj_event = value


  def to_dict(self):
    """
    Return persona's scratch as a dictionary. 
    """
    scratch = dict() 
    scratch["vision_r"] = self.vision_r
    scratch["att_bandwidth"] = self.att_bandwidth
    scratch["retention"] = self.retention

    scratch["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
    scratch["curr_tile"] = self.curr_tile.as_tuple() if self.curr_tile else None
    scratch["daily_plan_req"] = self.daily_plan_req

    scratch["name"] = self.name
    scratch["first_name"] = self.first_name
    scratch["last_name"] = self.last_name
    scratch["age"] = self.age
    scratch["innate"] = self.innate
    scratch["learned"] = self.learned
    scratch["currently"] = self.currently
    scratch["lifestyle"] = self.lifestyle
    scratch["living_area"] = self.living_area

    scratch["concept_forget"] = self.concept_forget
    scratch["daily_reflection_time"] = self.daily_reflection_time
    scratch["daily_reflection_size"] = self.daily_reflection_size
    scratch["overlap_reflect_th"] = self.overlap_reflect_th
    scratch["kw_strg_event_reflect_th"] = self.kw_strg_event_reflect_th
    scratch["kw_strg_thought_reflect_th"] = self.kw_strg_thought_reflect_th

    scratch["recency_w"] = self.recency_w
    scratch["relevance_w"] = self.relevance_w
    scratch["importance_w"] = self.importance_w
    scratch["recency_decay"] = self.recency_decay
    scratch["importance_trigger_max"] = self.importance_trigger_max
    scratch["importance_trigger_curr"] = self.importance_trigger_curr
    scratch["importance_ele_n"] = self.importance_ele_n
    scratch["thought_count"] = self.thought_count

    scratch["daily_req"] = self.daily_req
    scratch["f_daily_schedule"] = [[x.description, x.duration] for x in self.f_daily_schedule]
    scratch["f_daily_schedule_hourly_org"] = [[x.description, x.duration] for x in self.f_daily_schedule_hourly_org]

    scratch["act_address"] = self.act_address
    scratch["act_start_time"] = (self.act_start_time.strftime("%B %d, %Y, %H:%M:%S") 
                                 if self.act_start_time else None)
    scratch["act_duration"] = self.act_duration
    scratch["act_description"] = self.act_description
    scratch["act_pronunciatio"] = self.act_pronunciatio
    scratch["act_event"] = self.act_event

    scratch["act_obj_description"] = self.act_obj_description
    scratch["act_obj_pronunciatio"] = self.act_obj_pronunciatio
    scratch["act_obj_event"] = self.act_obj_event

    scratch["chatting_with"] = self.chatting_with
    scratch["chat"] = self.chat
    scratch["chatting_with_buffer"] = self.chatting_with_buffer
    if self.chatting_end_time: 
      scratch["chatting_end_time"] = (self.chatting_end_time
                                        .strftime("%B %d, %Y, %H:%M:%S"))
    else: 
      scratch["chatting_end_time"] = None

    scratch["act_path_set"] = self.act_path_set
    scratch["planned_path"] = [p.as_tuple() for p in self.planned_path]
    
    return scratch 


  def get_f_daily_schedule_index(self, advance=0):
    """
    We get the current index of self.f_daily_schedule. 

    Recall that self.f_daily_schedule stores the decomposed action sequences 
    up until now, and the hourly sequences of the future action for the rest
    of today. Given that self.f_daily_schedule is a list of list where the 
    inner list is composed of [task, duration], we continue to add up the 
    duration until we reach "if elapsed > today_min_elapsed" condition. The
    index where we stop is the index we will return. 

    INPUT
      advance: Integer value of the number minutes we want to look into the 
               future. This allows us to get the index of a future timeframe.
    OUTPUT 
      an integer value for the current index of f_daily_schedule.
    """
    # We first calculate teh number of minutes elapsed today. 
    today_min_elapsed = 0
    today_min_elapsed += self.curr_time.hour * 60
    today_min_elapsed += self.curr_time.minute
    today_min_elapsed += advance

    x = 0
    for task, duration in self.f_daily_schedule: 
      x += duration
    x = 0
    for task, duration in self.f_daily_schedule_hourly_org: 
      x += duration

    # We then calculate the current index based on that. 
    curr_index = 0
    elapsed = 0
    for task, duration in self.f_daily_schedule: 
      elapsed += duration
      if elapsed > today_min_elapsed: 
        return curr_index
      curr_index += 1

    return curr_index


  def get_f_daily_schedule_hourly_org_index(self, advance=0):
    """
    We get the current index of self.f_daily_schedule_hourly_org. 
    It is otherwise the same as get_f_daily_schedule_index. 

    INPUT
      advance: Integer value of the number minutes we want to look into the 
               future. This allows us to get the index of a future timeframe.
    OUTPUT 
      an integer value for the current index of f_daily_schedule.
    """
    # We first calculate teh number of minutes elapsed today. 
    today_min_elapsed = 0
    today_min_elapsed += self.curr_time.hour * 60
    today_min_elapsed += self.curr_time.minute
    today_min_elapsed += advance
    # We then calculate the current index based on that. 
    curr_index = 0
    elapsed = 0
    for task, duration in self.f_daily_schedule_hourly_org: 
      elapsed += duration
      if elapsed > today_min_elapsed: 
        return curr_index
      curr_index += 1
    return curr_index


  def get_str_iss(self): 
    """
    ISS stands for "identity stable set." This describes the commonset summary
    of this persona -- basically, the bare minimum description of the persona
    that gets used in almost all prompts that need to call on the persona. 

    INPUT
      None
    OUTPUT
      the identity stable set summary of the persona in a string form.
    EXAMPLE STR OUTPUT
      "Name: Dolores Heitmiller
       Age: 28
       Innate traits: hard-edged, independent, loyal
       Learned traits: Dolores is a painter who wants live quietly and paint 
         while enjoying her everyday life.
       Currently: Dolores is preparing for her first solo show. She mostly 
         works from home.
       Lifestyle: Dolores goes to bed around 11pm, sleeps for 7 hours, eats 
         dinner around 6pm.
       Daily plan requirement: Dolores is planning to stay at home all day and 
         never go out."
    """
    commonset = ""
    commonset += f"Name: {self.name}\n"
    commonset += f"Age: {self.age}\n"
    commonset += f"Innate traits: {self.innate}\n"
    commonset += f"Learned traits: {self.learned}\n"
    commonset += f"Currently: {self.currently}\n"
    commonset += f"Lifestyle: {self.lifestyle}\n"
    commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
    commonset += f"Current Date: {self.curr_time.strftime('%A %B %d')}\n"
    return commonset


  def get_str_name(self): 
    return self.name


  def get_str_firstname(self): 
    return self.first_name


  def get_str_lastname(self): 
    return self.last_name


  def get_str_age(self): 
    return str(self.age)


  def get_str_innate(self): 
    return self.innate


  def get_str_learned(self): 
    return self.learned


  def get_str_currently(self): 
    return self.currently


  def get_str_lifestyle(self): 
    return self.lifestyle


  def get_str_daily_plan_req(self): 
    return self.daily_plan_req


  def get_str_curr_date_str(self): 
    return self.curr_time.strftime("%A %B %d")


  def get_curr_event(self):
    if not self.act_address: 
      return (self.name, None, None)
    else: 
      return self.act_event


  def get_curr_event_and_desc(self): 
    if not self.act_address: 
      return (self.name, None, None, None)
    else: 
      return (self.act_event[0], 
              self.act_event[1], 
              self.act_event[2],
              self.act_description)


  def get_curr_obj_event_and_desc(self): 
    if not self.act_address: 
      return ("", None, None, None)
    else: 
      return (self.act_address, 
              self.act_obj_event[1], 
              self.act_obj_event[2],
              self.act_obj_description)


  def add_new_action(self, 
                     action_address, 
                     action_duration,
                     action_description,
                     action_pronunciatio, 
                     action_event,
                     chatting_with, 
                     chat, 
                     chatting_with_buffer,
                     chatting_end_time,
                     act_obj_description, 
                     act_obj_pronunciatio, 
                     act_obj_event, 
                     act_start_time=None): 
    self.act_address = action_address
    self.act_duration = action_duration
    self.act_description = action_description
    self.act_pronunciatio = action_pronunciatio
    self.act_event = action_event

    self.chatting_with = chatting_with
    self.chat = chat 
    if chatting_with_buffer: 
      self.chatting_with_buffer.update(chatting_with_buffer)
    self.chatting_end_time = chatting_end_time

    self.act_obj_description = act_obj_description
    self.act_obj_pronunciatio = act_obj_pronunciatio
    self.act_obj_event = act_obj_event
    
    self.act_start_time = self.curr_time
    
    self.act_path_set = False


  def act_time_str(self): 
    """
    Returns a string output of the current time. 

    INPUT
      None
    OUTPUT 
      A string output of the current time.
    EXAMPLE STR OUTPUT
      "14:05 P.M."
    """
    return self.act_start_time.strftime("%H:%M %p")


  def get_current_action(self):
    """
    Returns the current action as a CurrentAction object.
    Used for building AgentContext snapshots.
    
    Returns:
        CurrentAction: The current action state, or None if no action is set.
    """
    if not self.act_address:
      return None
    return self.act


  def act_check_finished(self): 
    """
    Checks whether the self.Action instance has finished.  

    INPUT
      curr_datetime: Current time. If current time is later than the action's
                     start time + its duration, then the action has finished. 
    OUTPUT 
      Boolean [True]: Action has finished.
      Boolean [False]: Action has not finished and is still ongoing.
    """
    if not self.act_address: 
      return True
      
    if self.chatting_with: 
      end_time = self.chatting_end_time
    else: 
      x = self.act_start_time
      if x.second != 0: 
        x = x.replace(second=0)
        x = (x + datetime.timedelta(minutes=1))
      end_time = (x + datetime.timedelta(minutes=self.act_duration))

    if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"): 
      return True
    return False


  def act_summarize(self):
    """
    Summarize the current action as a dictionary. 

    INPUT
      None
    OUTPUT 
      ret: A human readable summary of the action.
    """
    exp = dict()
    exp["persona"] = self.name
    exp["address"] = self.act_address
    exp["start_datetime"] = self.act_start_time
    exp["duration"] = self.act_duration
    exp["description"] = self.act_description
    exp["pronunciatio"] = self.act_pronunciatio
    return exp


  def act_summary_str(self):
    """
    Returns a string summary of the current action. Meant to be 
    human-readable.

    INPUT
      None
    OUTPUT 
      ret: A human readable summary of the action.
    """
    start_datetime_str = self.act_start_time.strftime("%A %B %d -- %H:%M %p")
    ret = f"[{start_datetime_str}]\n"
    ret += f"Activity: {self.name} is {self.act_description}\n"
    ret += f"Address: {self.act_address}\n"
    ret += f"Duration in minutes (e.g., x min): {str(self.act_duration)} min\n"
    return ret


  def get_str_daily_schedule_summary(self): 
    ret = ""
    curr_min_sum = 0
    for row in self.f_daily_schedule: 
      curr_min_sum += row[1]
      hour = int(curr_min_sum/60)
      minute = curr_min_sum%60
      ret += f"{hour:02}:{minute:02} || {row[0]}\n"
    return ret


  def get_str_daily_schedule_hourly_org_summary(self): 
    ret = ""
    curr_min_sum = 0
    for row in self.f_daily_schedule_hourly_org: 
      curr_min_sum += row[1]
      hour = int(curr_min_sum/60)
      minute = curr_min_sum%60
      ret += f"{hour:02}:{minute:02} || {row[0]}\n"
    return ret




















