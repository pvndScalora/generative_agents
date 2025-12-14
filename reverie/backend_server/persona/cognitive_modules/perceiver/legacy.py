import math
import logging
from operator import itemgetter
from .base import AbstractPerceiver
from persona.prompt_template.gpt_structure import get_embedding
from persona.prompt_template.run_gpt_prompt import run_gpt_prompt_event_poignancy, run_gpt_prompt_chat_poignancy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from persona.persona import Persona
    from persona.memory_structures.scratch import Scratch
    from reverie.backend_server.maze import Maze

class LegacyPerceiver(AbstractPerceiver):
    def __init__(self, scratch: "Scratch"):
        self.scratch = scratch

    def perceive(self, maze: "Maze"):
        """
        Perceives events around the persona and saves it to the memory, both events 
        and spaces. 
        """
        # PERCEIVE SPACE
        nearby_tiles = maze.get_nearby_tiles(self.scratch.curr_tile, 
                                            self.scratch.vision_r)

        for i in nearby_tiles: 
            i = maze.access_tile(i)
            if i["world"]: 
                if (i["world"] not in self.scratch.s_mem.tree): 
                    self.scratch.s_mem.tree[i["world"]] = {}
            if i["sector"]: 
                if (i["sector"] not in self.scratch.s_mem.tree[i["world"]]): 
                    self.scratch.s_mem.tree[i["world"]][i["sector"]] = {}
            if i["arena"]: 
                if (i["arena"] not in self.scratch.s_mem.tree[i["world"]]
                                                        [i["sector"]]): 
                    self.scratch.s_mem.tree[i["world"]][i["sector"]][i["arena"]] = []
            if i["game_object"]: 
                if (i["game_object"] not in self.scratch.s_mem.tree[i["world"]]
                                                                [i["sector"]]
                                                                [i["arena"]]): 
                    self.scratch.s_mem.tree[i["world"]][i["sector"]][i["arena"]] += [
                                                                        i["game_object"]]

        # PERCEIVE EVENTS. 
        curr_arena_path = maze.get_tile_path(self.scratch.curr_tile, "arena")
        percept_events_set = set()
        percept_events_list = []
        
        for tile in nearby_tiles: 
            tile_details = maze.access_tile(tile)
            if tile_details["events"]: 
                if maze.get_tile_path(tile, "arena") == curr_arena_path:  
                    dist = math.dist([tile[0], tile[1]], 
                                    [self.scratch.curr_tile[0], 
                                    self.scratch.curr_tile[1]])
                    for event in tile_details["events"]: 
                        if event not in percept_events_set: 
                            percept_events_list += [[dist, event]]
                            percept_events_set.add(event)

        percept_events_list = sorted(percept_events_list, key=itemgetter(0))
        perceived_events = []
        for dist, event in percept_events_list[:self.scratch.att_bandwidth]: 
            perceived_events += [event]

        ret_events = []
        for p_event in perceived_events: 
            s, p, o, desc = p_event
            if not p: 
                p = "is"
                o = "idle"
                desc = "idle"
            desc = f"{s.split(':')[-1]} is {desc}"
            p_event = (s, p, o)

            latest_events = self.scratch.a_mem.get_summarized_latest_events(
                                            self.scratch.retention)
            if p_event not in latest_events:
                keywords = set()
                sub = p_event[0]
                obj = p_event[2]
                if ":" in p_event[0]: 
                    sub = p_event[0].split(":")[-1]
                if ":" in p_event[2]: 
                    obj = p_event[2].split(":")[-1]
                keywords.update([sub, obj])

                desc_embedding_in = desc
                if "(" in desc: 
                    desc_embedding_in = (desc_embedding_in.split("(")[1]
                                                        .split(")")[0]
                                                        .strip())
                if desc_embedding_in in self.scratch.a_mem.embeddings: 
                    event_embedding = self.scratch.a_mem.embeddings[desc_embedding_in]
                else: 
                    event_embedding = get_embedding(desc_embedding_in)
                event_embedding_pair = (desc_embedding_in, event_embedding)
                
                event_poignancy = self._generate_poig_score("event", desc_embedding_in)

                chat_node_ids = []
                if p_event[0] == f"{self.scratch.name}" and p_event[1] == "chat with": 
                    curr_event = self.scratch.act_event
                    if self.scratch.act_description in self.scratch.a_mem.embeddings: 
                        chat_embedding = self.scratch.a_mem.embeddings[
                                            self.scratch.act_description]
                    else: 
                        chat_embedding = get_embedding(self.scratch
                                                                .act_description)
                    chat_embedding_pair = (self.scratch.act_description, 
                                        chat_embedding)
                    chat_poignancy = self._generate_poig_score("chat", 
                                                        self.scratch.act_description)
                    chat_node = self.scratch.a_mem.add_chat(self.scratch.curr_time, None,
                                curr_event[0], curr_event[1], curr_event[2], 
                                self.scratch.act_description, keywords, 
                                chat_poignancy, chat_embedding_pair, 
                                self.scratch.chat)
                    chat_node_ids = [chat_node.node_id]

                ret_events += [self.scratch.a_mem.add_event(self.scratch.curr_time, None,
                                    s, p, o, desc, keywords, event_poignancy, 
                                    event_embedding_pair, chat_node_ids)]
                self.scratch.importance_trigger_curr -= event_poignancy
                self.scratch.importance_ele_n += 1

        return ret_events

    def _generate_poig_score(self, event_type, description): 
        if "is idle" in description: 
            return 1

        if event_type == "event": 
            return run_gpt_prompt_event_poignancy(self.scratch, description)[0]
        elif event_type == "chat": 
            return run_gpt_prompt_chat_poignancy(self.scratch, 
                                self.scratch.act_description)[0]
