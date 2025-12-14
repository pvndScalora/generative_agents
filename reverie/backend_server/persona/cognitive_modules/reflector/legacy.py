import datetime
import random
import logging

from numpy import dot
from numpy.linalg import norm

from persona.prompt_template.run_gpt_prompt import *
from persona.prompt_template.gpt_structure import *
from .base import AbstractReflector
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from persona.memory_structures.scratch import Scratch
    from persona.cognitive_modules.retriever.base import AbstractRetriever

class LegacyReflector(AbstractReflector):
    def __init__(self, scratch: "Scratch", retriever: "AbstractRetriever"):
        self.scratch = scratch
        self.retriever = retriever

    def reflect(self):
        """
        The main reflection module for the persona. We first check if the trigger 
        conditions are met, and if so, run the reflection and reset any of the 
        relevant counters. 
        """
        if self._reflection_trigger(): 
            self._run_reflect()
            self._reset_reflection_counter()

        if self.scratch.chatting_end_time: 
            if self.scratch.curr_time + datetime.timedelta(0,10) == self.scratch.chatting_end_time: 
                all_utt = ""
                if self.scratch.chat: 
                    for row in self.scratch.chat:  
                        all_utt += f"{row[0]}: {row[1]}\n"

                evidence = [self.scratch.a_mem.get_last_chat(self.scratch.chatting_with).node_id]

                planning_thought = self._generate_planning_thought_on_convo(all_utt)
                planning_thought = f"For {self.scratch.name}'s planning: {planning_thought}"

                created = self.scratch.curr_time
                expiration = self.scratch.curr_time + datetime.timedelta(days=30)
                s, p, o = self._generate_action_event_triple(planning_thought)
                keywords = set([s, p, o])
                thought_poignancy = self._generate_poig_score("thought", planning_thought)
                thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

                self.scratch.a_mem.add_thought(created, expiration, s, p, o, 
                                            planning_thought, keywords, thought_poignancy, 
                                            thought_embedding_pair, evidence)

                memo_thought = self._generate_memo_on_convo(all_utt)
                memo_thought = f"{self.scratch.name} {memo_thought}"

                created = self.scratch.curr_time
                expiration = self.scratch.curr_time + datetime.timedelta(days=30)
                s, p, o = self._generate_action_event_triple(memo_thought)
                keywords = set([s, p, o])
                thought_poignancy = self._generate_poig_score("thought", memo_thought)
                thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

                self.scratch.a_mem.add_thought(created, expiration, s, p, o, 
                                            memo_thought, keywords, thought_poignancy, 
                                            thought_embedding_pair, evidence)

    def _reflection_trigger(self): 
        print (self.scratch.name, "persona.scratch.importance_trigger_curr::", self.scratch.importance_trigger_curr)
        print (self.scratch.importance_trigger_max)

        if (self.scratch.importance_trigger_curr <= 0 and 
            [] != self.scratch.a_mem.seq_event + self.scratch.a_mem.seq_thought): 
            return True 
        return False

    def _reset_reflection_counter(self): 
        persona_imt_max = self.scratch.importance_trigger_max
        self.scratch.importance_trigger_curr = persona_imt_max
        self.scratch.importance_ele_n = 0

    def _run_reflect(self):
        # Reflection requires certain focal points. Generate that first. 
        focal_points = self._generate_focal_points(3)
        # Retrieve the relevant Nodes object for each of the focal points. 
        retrieved = self.retriever.retrieve_weighted(focal_points)

        # For each of the focal points, generate thoughts and save it in the 
        # agent's memory. 
        for focal_pt, nodes in retrieved.items(): 
            xx = [i.embedding_key for i in nodes]
            for xxx in xx: print (xxx)

            thoughts = self._generate_insights_and_evidence(nodes, 5)
            for thought, evidence in thoughts.items(): 
                created = self.scratch.curr_time
                expiration = self.scratch.curr_time + datetime.timedelta(days=30)
                s, p, o = self._generate_action_event_triple(thought)
                keywords = set([s, p, o])
                thought_poignancy = self._generate_poig_score("thought", thought)
                thought_embedding_pair = (thought, get_embedding(thought))

                self.scratch.a_mem.add_thought(created, expiration, s, p, o, 
                                            thought, keywords, thought_poignancy, 
                                            thought_embedding_pair, evidence)

    def _generate_focal_points(self, n=3): 
        logging.debug("GNS FUNCTION: <generate_focal_points>")
        
        nodes = [[i.last_accessed, i]
                    for i in self.scratch.a_mem.seq_event + self.scratch.a_mem.seq_thought
                    if "idle" not in i.embedding_key]

        nodes = sorted(nodes, key=lambda x: x[0])
        nodes = [i for created, i in nodes]

        statements = ""
        for node in nodes[-1*self.scratch.importance_ele_n:]: 
            statements += node.embedding_key + "\n"

        return run_gpt_prompt_focal_pt(self.scratch, statements, n)[0]

    def _generate_insights_and_evidence(self, nodes, n=5): 
        logging.debug("GNS FUNCTION: <generate_insights_and_evidence>")

        statements = ""
        for count, node in enumerate(nodes): 
            statements += f'{str(count)}. {node.embedding_key}\n'

        ret = run_gpt_prompt_insight_and_guidance(self.scratch, statements, n)[0]

        print (ret)
        try: 
            for thought, evi_raw in ret.items(): 
                evidence_node_id = [nodes[i].node_id for i in evi_raw]
                ret[thought] = evidence_node_id
            return ret
        except: 
            return {"this is blank": "node_1"} 

    def _generate_action_event_triple(self, act_desp): 
        logging.debug("GNS FUNCTION: <generate_action_event_triple>")
        return run_gpt_prompt_event_triple(act_desp, self.scratch)[0]

    def _generate_poig_score(self, event_type, description): 
        logging.debug("GNS FUNCTION: <generate_poig_score>")

        if "is idle" in description: 
            return 1

        if event_type == "event" or event_type == "thought": 
            return run_gpt_prompt_event_poignancy(self.scratch, description)[0]
        elif event_type == "chat": 
            return run_gpt_prompt_chat_poignancy(self.scratch, 
                                self.scratch.act_description)[0]

    def _generate_planning_thought_on_convo(self, all_utt):
        logging.debug("GNS FUNCTION: <generate_planning_thought_on_convo>")
        return run_gpt_prompt_planning_thought_on_convo(self.scratch, all_utt)[0]

    def _generate_memo_on_convo(self, all_utt):
        logging.debug("GNS FUNCTION: <generate_memo_on_convo>")
        return run_gpt_prompt_memo_on_convo(self.scratch, all_utt)[0]
