import datetime
import math
import random
import logging
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from persona.persona import Persona
    from persona.memory_structures.scratch import Scratch

from reverie.backend_server.models import Action
from reverie.backend_server.persona.prompt_template.run_gpt_prompt import (
    run_gpt_prompt_wake_up_hour,
    run_gpt_prompt_daily_plan,
    run_gpt_prompt_generate_hourly_schedule,
    run_gpt_prompt_task_decomp,
    run_gpt_prompt_action_sector,
    run_gpt_prompt_action_arena,
    run_gpt_prompt_action_game_object,
    run_gpt_prompt_pronunciatio,
    run_gpt_prompt_event_triple,
    run_gpt_prompt_act_obj_desc,
    run_gpt_prompt_act_obj_event_triple,
    run_gpt_prompt_summarize_conversation,
    run_gpt_prompt_decide_to_talk,
    run_gpt_prompt_decide_to_react,
    run_gpt_prompt_new_decomp_schedule,
    ChatGPT_single_request
)
from reverie.backend_server.persona.prompt_template.gpt_structure import get_embedding
# from reverie.backend_server.persona.cognitive_modules.converse import agent_chat_v2
from .base import AbstractPlanner

class LegacyPlanner(AbstractPlanner):
    """
    The legacy implementation of the planning module.
    Includes long-term planning (daily schedule), short-term planning (next action),
    and reaction to perceived events.
    """

    def __init__(self, scratch: "Scratch", retriever: Any, converser: Any):
        self.scratch = scratch
        self.retriever = retriever
        self.converser = converser

    def plan(self, maze: "Maze", personas: Dict[str, "Persona"], new_day: Any, retrieved: Dict[str, Dict[str, Any]]) -> str:
        """
        Main cognitive function for planning.
        """
        # PART 1: Generate the hourly schedule. 
        if new_day: 
            self._long_term_planning(new_day)

        # PART 2: If the current action has expired, we want to create a new plan.
        if self.scratch.act_check_finished(): 
            self._determine_action(maze)

        # PART 3: If you perceived an event that needs to be responded to
        focused_event = False
        if retrieved.keys(): 
            focused_event = self._choose_retrieved(retrieved)
        
        if focused_event: 
            reaction_mode = self._should_react(focused_event, personas)
            if reaction_mode: 
                if reaction_mode[:9] == "chat with":
                    self._chat_react(maze, focused_event, reaction_mode, personas)
                elif reaction_mode[:4] == "wait": 
                    self._wait_react(reaction_mode)

        # Step 3: Chat-related state clean up. 
        if self.scratch.act_event[1] != "chat with":
            self.scratch.chatting_with = None
            self.scratch.chat = None
            self.scratch.chatting_end_time = None

        curr_persona_chat_buffer = self.scratch.chatting_with_buffer
        for persona_name, buffer_count in curr_persona_chat_buffer.items():
            if persona_name != self.scratch.chatting_with: 
                self.scratch.chatting_with_buffer[persona_name] -= 1

        return self.scratch.act_address

    def _long_term_planning(self, new_day): 
        wake_up_hour = self._generate_wake_up_hour()

        if new_day == "First day": 
            self.scratch.daily_req = self._generate_first_daily_plan(wake_up_hour)
        elif new_day == "New day":
            self._revise_identity()
            self.scratch.daily_req = self.scratch.daily_req

        self.scratch.f_daily_schedule = self._generate_hourly_schedule(wake_up_hour)
        self.scratch.f_daily_schedule_hourly_org = (self.scratch.f_daily_schedule[:])

        thought = f"This is {self.scratch.name}'s plan for {self.scratch.curr_time.strftime('%A %B %d')}:"
        for i in self.scratch.daily_req: 
            thought += f" {i},"
        thought = thought[:-1] + "."
        created = self.scratch.curr_time
        expiration = self.scratch.curr_time + datetime.timedelta(days=30)
        s, p, o = (self.scratch.name, "plan", self.scratch.curr_time.strftime('%A %B %d'))
        keywords = set(["plan"])
        thought_poignancy = 5
        thought_embedding_pair = (thought, get_embedding(thought))
        self.scratch.a_mem.add_thought(created, expiration, s, p, o, 
                                    thought, keywords, thought_poignancy, 
                                    thought_embedding_pair, None)

    def _determine_action(self, maze): 
        def determine_decomp(act_desp, act_dura):
            if "sleep" not in act_desp and "bed" not in act_desp: 
                return True
            elif "sleeping" in act_desp or "asleep" in act_desp or "in bed" in act_desp:
                return False
            elif "sleep" in act_desp or "bed" in act_desp: 
                if act_dura > 60: 
                    return False
            return True

        curr_index = self.scratch.get_f_daily_schedule_index()
        curr_index_60 = self.scratch.get_f_daily_schedule_index(advance=60)

        if curr_index == 0:
            act_desp, act_dura = self.scratch.f_daily_schedule[curr_index]
            if act_dura >= 60: 
                if determine_decomp(act_desp, act_dura): 
                    self.scratch.f_daily_schedule[curr_index:curr_index+1] = (
                                        self._generate_task_decomp(act_desp, act_dura))
            if curr_index_60 + 1 < len(self.scratch.f_daily_schedule):
                act_desp, act_dura = self.scratch.f_daily_schedule[curr_index_60+1]
                if act_dura >= 60: 
                    if determine_decomp(act_desp, act_dura): 
                        self.scratch.f_daily_schedule[curr_index_60+1:curr_index_60+2] = (
                                            self._generate_task_decomp(act_desp, act_dura))

        if curr_index_60 < len(self.scratch.f_daily_schedule):
            if self.scratch.curr_time.hour < 23:
                act_desp, act_dura = self.scratch.f_daily_schedule[curr_index_60]
                if act_dura >= 60: 
                    if determine_decomp(act_desp, act_dura): 
                        self.scratch.f_daily_schedule[curr_index_60:curr_index_60+1] = (
                                            self._generate_task_decomp(act_desp, act_dura))

        x_emergency = 0
        for i in self.scratch.f_daily_schedule: 
            x_emergency += i.duration

        if 1440 - x_emergency > 0: 
            self.scratch.f_daily_schedule += [Action(description="sleeping", duration=1440 - x_emergency)]
        
        act_desp, act_dura = self.scratch.f_daily_schedule[curr_index] 

        act_world = maze.access_tile(self.scratch.curr_tile)["world"]
        act_sector = self._generate_action_sector(act_desp, maze)
        act_arena = self._generate_action_arena(act_desp, maze, act_world, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_arena}"
        act_game_object = self._generate_action_game_object(act_desp, act_address, maze)
        new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
        act_pron = self._generate_action_pronunciatio(act_desp)
        act_event = self._generate_action_event_triple(act_desp)
        
        act_obj_desp = self._generate_act_obj_desc(act_game_object, act_desp)
        act_obj_pron = self._generate_action_pronunciatio(act_obj_desp)
        act_obj_event = self._generate_act_obj_event_triple(act_game_object, act_obj_desp)

        self.scratch.add_new_action(new_address, 
                                        int(act_dura), 
                                        act_desp, 
                                        act_pron, 
                                        act_event,
                                        None,
                                        None,
                                        None,
                                        None,
                                        act_obj_desp, 
                                        act_obj_pron, 
                                        act_obj_event)

    def _choose_retrieved(self, retrieved): 
        copy_retrieved = retrieved.copy()
        for event_desc, rel_ctx in copy_retrieved.items(): 
            curr_event = rel_ctx["curr_event"]
            if curr_event.subject == self.scratch.name: 
                del retrieved[event_desc]

        priority = []
        for event_desc, rel_ctx in retrieved.items(): 
            curr_event = rel_ctx["curr_event"]
            if (":" not in curr_event.subject 
                and curr_event.subject != self.scratch.name): 
                priority += [rel_ctx]
        if priority: 
            return random.choice(priority)

        for event_desc, rel_ctx in retrieved.items(): 
            curr_event = rel_ctx["curr_event"]
            if "is idle" not in event_desc: 
                priority += [rel_ctx]
        if priority: 
            return random.choice(priority)
        return None

    def _should_react(self, retrieved, personas): 
        def lets_talk(init_persona, target_persona, retrieved):
            if (not target_persona.scratch.act_address 
                or not target_persona.scratch.act_description
                or not init_persona.scratch.act_address
                or not init_persona.scratch.act_description): 
                return False

            if ("sleeping" in target_persona.scratch.act_description 
                or "sleeping" in init_persona.scratch.act_description): 
                return False

            if init_persona.scratch.curr_time.hour == 23: 
                return False

            if "<waiting>" in target_persona.scratch.act_address: 
                return False

            if (target_persona.scratch.chatting_with 
                or init_persona.scratch.chatting_with): 
                return False

            if (target_persona.name in init_persona.scratch.chatting_with_buffer): 
                if init_persona.scratch.chatting_with_buffer[target_persona.name] > 0: 
                    return False

            # NOTE: run_gpt_prompt_decide_to_talk expects a persona object.
            # We pass init_persona which is self.persona (now self.scratch).
            # self.scratch has a .scratch property that returns self, so it mimics persona.
            if run_gpt_prompt_decide_to_talk(init_persona, target_persona, retrieved)[0] == "yes": 
                return True

            return False

        def lets_react(init_persona, target_persona, retrieved): 
            if (not target_persona.scratch.act_address 
                or not target_persona.scratch.act_description
                or not init_persona.scratch.act_address
                or not init_persona.scratch.act_description): 
                return False

            if ("sleeping" in target_persona.scratch.act_description 
                or "sleeping" in init_persona.scratch.act_description): 
                return False

            if init_persona.scratch.curr_time.hour == 23: 
                return False

            if "waiting" in target_persona.scratch.act_description: 
                return False
            if init_persona.scratch.planned_path == []:
                return False

            if (init_persona.scratch.act_address 
                != target_persona.scratch.act_address): 
                return False

            react_mode = run_gpt_prompt_decide_to_react(init_persona, target_persona, retrieved)[0]

            if react_mode == "1": 
                wait_until = ((target_persona.scratch.act_start_time 
                    + datetime.timedelta(minutes=target_persona.scratch.act_duration - 1))
                    .strftime("%B %d, %Y, %H:%M:%S"))
                return f"wait: {wait_until}"
            elif react_mode == "2":
                return False
            else:
                return False 

        if self.scratch.chatting_with: 
            return False
        if "<waiting>" in self.scratch.act_address: 
            return False

        curr_event = retrieved["curr_event"]

        if ":" not in curr_event.subject: 
            # Pass self.scratch as init_persona
            if lets_talk(self.scratch, personas[curr_event.subject], retrieved):
                return f"chat with {curr_event.subject}"
            react_mode = lets_react(self.scratch, personas[curr_event.subject], retrieved)
            return react_mode
        return False

    def _create_react(self, inserted_act, inserted_act_dur,
                    act_address, act_event, chatting_with, chat, chatting_with_buffer,
                    chatting_end_time, 
                    act_pronunciatio, act_obj_description, act_obj_pronunciatio, 
                    act_obj_event, act_start_time=None): 
        p = self.scratch # Use scratch as persona proxy

        min_sum = 0
        for i in range (p.get_f_daily_schedule_hourly_org_index()): 
            min_sum += p.f_daily_schedule_hourly_org[i].duration
        start_hour = int (min_sum/60)

        if (p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()].duration >= 120):
            end_hour = start_hour + p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()].duration/60

        elif (p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()].duration + 
            p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()+1].duration): 
            end_hour = start_hour + ((p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()].duration + 
                    p.f_daily_schedule_hourly_org[p.get_f_daily_schedule_hourly_org_index()+1].duration)/60)

        else: 
            end_hour = start_hour + 2
        end_hour = int(end_hour)

        dur_sum = 0
        count = 0 
        start_index = None
        end_index = None
        for act in p.f_daily_schedule: 
            if dur_sum >= start_hour * 60 and start_index == None:
                start_index = count
            if dur_sum >= end_hour * 60 and end_index == None: 
                end_index = count
            dur_sum += act.duration
            count += 1

        ret = self._generate_new_decomp_schedule(inserted_act, inserted_act_dur, start_hour, end_hour)
        p.f_daily_schedule[start_index:end_index] = ret
        p.add_new_action(act_address,
                            inserted_act_dur,
                            inserted_act,
                            act_pronunciatio,
                            act_event,
                            chatting_with,
                            chat,
                            chatting_with_buffer,
                            chatting_end_time,
                            act_obj_description,
                            act_obj_pronunciatio,
                            act_obj_event,
                            act_start_time)

    def _chat_react(self, maze, focused_event, reaction_mode, personas):
        init_persona = self.scratch # Use scratch as persona proxy
        target_persona = personas[reaction_mode[9:].strip()]

        convo, duration_min = self._generate_convo(maze, init_persona, target_persona)
        convo_summary = self._generate_convo_summary(convo)
        inserted_act = convo_summary
        inserted_act_dur = duration_min

        act_start_time = target_persona.scratch.act_start_time

        curr_time = target_persona.scratch.curr_time
        if curr_time.second != 0: 
            temp_curr_time = curr_time + datetime.timedelta(seconds=60 - curr_time.second)
            chatting_end_time = temp_curr_time + datetime.timedelta(minutes=inserted_act_dur)
        else: 
            chatting_end_time = curr_time + datetime.timedelta(minutes=inserted_act_dur)

        act_address = f"<persona> {target_persona.name}"
        act_event = (init_persona.name, "chat with", target_persona.name)
        chatting_with = target_persona.name
        chatting_with_buffer = {}
        chatting_with_buffer[target_persona.name] = 800

        act_pronunciatio = "💬" 
        act_obj_description = None
        act_obj_pronunciatio = None
        act_obj_event = (None, None, None)

        self._create_react(inserted_act, inserted_act_dur,
            act_address, act_event, chatting_with, convo, chatting_with_buffer, chatting_end_time,
            act_pronunciatio, act_obj_description, act_obj_pronunciatio, 
            act_obj_event, act_start_time)

    def _wait_react(self, reaction_mode): 
        p = self.scratch

        inserted_act = f'waiting to start {p.act_description.split("(")[-1][:-1]}'
        end_time = datetime.datetime.strptime(reaction_mode[6:].strip(), "%B %d, %Y, %H:%M:%S")
        inserted_act_dur = (end_time.minute + end_time.hour * 60) - (p.curr_time.minute + p.curr_time.hour * 60) + 1

        act_address = f"<waiting> {p.curr_tile[0]} {p.curr_tile[1]}"
        act_event = (p.name, "waiting to start", p.act_description.split("(")[-1][:-1])
        chatting_with = None
        chat = None
        chatting_with_buffer = None
        chatting_end_time = None

        act_pronunciatio = "⌛" 
        act_obj_description = None
        act_obj_pronunciatio = None
        act_obj_event = (None, None, None)

        self._create_react(inserted_act, inserted_act_dur,
            act_address, act_event, chatting_with, chat, chatting_with_buffer, chatting_end_time,
            act_pronunciatio, act_obj_description, act_obj_pronunciatio, act_obj_event)

    # --- Helper Methods (Wrappers around GPT prompts) ---

    def _generate_wake_up_hour(self):
        logging.debug("GNS FUNCTION: <generate_wake_up_hour>")
        return int(run_gpt_prompt_wake_up_hour(self.scratch)[0])

    def _generate_first_daily_plan(self, wake_up_hour):
        logging.debug("GNS FUNCTION: <generate_first_daily_plan>")
        return run_gpt_prompt_daily_plan(self.scratch, wake_up_hour)[0]

    def _generate_hourly_schedule(self, wake_up_hour):
        logging.debug("GNS FUNCTION: <generate_hourly_schedule>")
        hour_str = ["00:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", 
                    "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", 
                    "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", 
                    "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM",
                    "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"]
        n_m1_activity = []
        diversity_repeat_count = 3
        for i in range(diversity_repeat_count): 
            n_m1_activity_set = set(n_m1_activity)
            if len(n_m1_activity_set) < 5: 
                n_m1_activity = []
                for count, curr_hour_str in enumerate(hour_str): 
                    if wake_up_hour > 0: 
                        n_m1_activity += ["sleeping"]
                        wake_up_hour -= 1
                    else: 
                        n_m1_activity += [run_gpt_prompt_generate_hourly_schedule(
                                        self.scratch, curr_hour_str, n_m1_activity, hour_str)[0]]
        
        _n_m1_hourly_compressed = []
        prev = None 
        prev_count = 0
        for i in n_m1_activity: 
            if i != prev:
                prev_count = 1 
                _n_m1_hourly_compressed += [[i, prev_count]]
                prev = i
            else: 
                if _n_m1_hourly_compressed: 
                    _n_m1_hourly_compressed[-1][1] += 1

        n_m1_hourly_compressed = []
        for task, duration in _n_m1_hourly_compressed: 
            n_m1_hourly_compressed.append(Action(description=task, duration=duration*60))

        return n_m1_hourly_compressed

    def _generate_task_decomp(self, task, duration):
        logging.debug("GNS FUNCTION: <generate_task_decomp>")
        ret = run_gpt_prompt_task_decomp(self.scratch, task, duration)[0]
        return [Action(description=x[0], duration=x[1]) for x in ret]

    def _generate_action_sector(self, act_desp, maze):
        logging.debug("GNS FUNCTION: <generate_action_sector>")
        return run_gpt_prompt_action_sector(act_desp, self.scratch, maze)[0]

    def _generate_action_arena(self, act_desp, maze, act_world, act_sector):
        logging.debug("GNS FUNCTION: <generate_action_arena>")
        return run_gpt_prompt_action_arena(act_desp, self.scratch, maze, act_world, act_sector)[0]

    def _generate_action_game_object(self, act_desp, act_address, maze):
        logging.debug("GNS FUNCTION: <generate_action_game_object>")
        if not self.scratch.s_mem.get_str_accessible_arena_game_objects(act_address): 
            return "<random>"
        return run_gpt_prompt_action_game_object(act_desp, self.scratch, maze, act_address)[0]

    def _generate_action_pronunciatio(self, act_desp):
        logging.debug("GNS FUNCTION: <generate_action_pronunciatio>")
        try: 
            x = run_gpt_prompt_pronunciatio(act_desp, self.scratch)[0]
        except: 
            x = "🙂"
        if not x: return "🙂"
        return x

    def _generate_action_event_triple(self, act_desp):
        logging.debug("GNS FUNCTION: <generate_action_event_triple>")
        return run_gpt_prompt_event_triple(act_desp, self.scratch)[0]

    def _generate_act_obj_desc(self, act_game_object, act_desp):
        logging.debug("GNS FUNCTION: <generate_act_obj_desc>")
        return run_gpt_prompt_act_obj_desc(act_game_object, act_desp, self.scratch)[0]

    def _generate_act_obj_event_triple(self, act_game_object, act_obj_desc):
        logging.debug("GNS FUNCTION: <generate_act_obj_event_triple>")
        return run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, self.scratch)[0]

    def _generate_convo(self, maze, init_persona, target_persona):
        # convo = agent_chat_v1(maze, init_persona, target_persona)
        # convo = agent_chat_v2(maze, init_persona, target_persona)
        convo = self.converser.chat(maze, target_persona)
        all_utt = ""
        for row in convo: 
            speaker = row[0]
            utt = row[1]
            all_utt += f"{speaker}: {utt}\n"
        convo_length = math.ceil(int(len(all_utt)/8) / 30)
        logging.debug("GNS FUNCTION: <generate_convo>")
        return convo, convo_length

    def _generate_convo_summary(self, convo):
        return run_gpt_prompt_summarize_conversation(self.scratch, convo)[0]

    def _generate_new_decomp_schedule(self, inserted_act, inserted_act_dur, start_hour, end_hour):
        p = self.scratch
        today_min_pass = (int(p.curr_time.hour) * 60 
                        + int(p.curr_time.minute) + 1)
        
        main_act_dur = []
        truncated_act_dur = []
        dur_sum = 0 
        count = 0 
        truncated_fin = False 

        for act in p.f_daily_schedule: 
            if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60): 
                main_act_dur += [[act.description, act.duration]]
                if dur_sum <= today_min_pass:
                    truncated_act_dur += [[act.description, act.duration]]
                elif dur_sum > today_min_pass and not truncated_fin: 
                    truncated_act_dur += [[p.f_daily_schedule[count].description, 
                                        dur_sum - today_min_pass]] 
                    truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass) 
                    truncated_fin = True
            dur_sum += act.duration
            count += 1

        x = truncated_act_dur[-1][0].split("(")[0].strip() + " (on the way to " + truncated_act_dur[-1][0].split("(")[-1][:-1] + ")"
        truncated_act_dur[-1][0] = x 

        if "(" in truncated_act_dur[-1][0]: 
            inserted_act = truncated_act_dur[-1][0].split("(")[0].strip() + " (" + inserted_act + ")"

        truncated_act_dur += [[inserted_act, inserted_act_dur]]
        start_time_hour = (datetime.datetime(2022, 10, 31, 0, 0) 
                        + datetime.timedelta(hours=start_hour))
        end_time_hour = (datetime.datetime(2022, 10, 31, 0, 0) 
                        + datetime.timedelta(hours=end_hour))

        logging.debug("GNS FUNCTION: <generate_new_decomp_schedule>")
        ret = run_gpt_prompt_new_decomp_schedule(self.scratch, 
                                                main_act_dur, 
                                                truncated_act_dur, 
                                                start_time_hour,
                                                end_time_hour,
                                                inserted_act,
                                                inserted_act_dur)[0]
        return [Action(description=x[0], duration=x[1]) for x in ret]

    def _revise_identity(self):
        p_name = self.scratch.name
        focal_points = [f"{p_name}'s plan for {self.scratch.get_str_curr_date_str()}.",
                        f"Important recent events for {p_name}'s life."]
        
        retrieved = self.retriever.retrieve_weighted(focal_points)

        statements = "[Statements]\n"
        for key, val in retrieved.items():
            for i in val: 
                statements += f"{i.created.strftime('%A %B %d -- %H:%M %p')}: {i.embedding_key}\n"

        plan_prompt = statements + "\n"
        plan_prompt += f"Given the statements above, is there anything that {p_name} should remember as they plan for"
        plan_prompt += f" *{self.scratch.curr_time.strftime('%A %B %d')}*? "
        plan_prompt += f"If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
        plan_prompt += f"Write the response from {p_name}'s perspective."
        plan_note = ChatGPT_single_request(plan_prompt)

        thought_prompt = statements + "\n"
        thought_prompt += f"Given the statements above, how might we summarize {p_name}'s feelings about their days up to now?\n\n"
        thought_prompt += f"Write the response from {p_name}'s perspective."
        thought_note = ChatGPT_single_request(thought_prompt)

        currently_prompt = f"{p_name}'s status from {(self.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
        currently_prompt += f"{self.scratch.currently}\n\n"
        currently_prompt += f"{p_name}'s thoughts at the end of {(self.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n" 
        currently_prompt += (plan_note + thought_note).replace('\n', '') + "\n\n"
        currently_prompt += f"It is now {self.scratch.curr_time.strftime('%A %B %d')}. Given the above, write {p_name}'s status for {self.scratch.curr_time.strftime('%A %B %d')} that reflects {p_name}'s thoughts at the end of {(self.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}. Write this in third-person talking about {p_name}."
        currently_prompt += f"If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement).\n\n"
        currently_prompt += "Follow this format below:\nStatus: <new status>"
        
        new_currently = ChatGPT_single_request(currently_prompt)
        self.scratch.currently = new_currently

        daily_req_prompt = self.scratch.get_str_iss() + "\n"
        daily_req_prompt += f"Today is {self.scratch.curr_time.strftime('%A %B %d')}. Here is {self.scratch.name}'s plan today in broad-strokes (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm).\n\n"
        daily_req_prompt += f"Follow this format (the list should have 4~6 items but no more):\n"
        daily_req_prompt += f"1. wake up and complete the morning routine at <time>, 2. ..."

        new_daily_req = ChatGPT_single_request(daily_req_prompt)
        new_daily_req = new_daily_req.replace('\n', ' ')
        self.scratch.daily_plan_req = new_daily_req
