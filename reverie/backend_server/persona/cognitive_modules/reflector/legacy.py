import datetime
import random
import logging
from typing import List, Optional, TYPE_CHECKING

from numpy import dot
from numpy.linalg import norm

from persona.prompt_template.run_gpt_prompt import *
from persona.prompt_template.gpt_structure import *
from reverie.backend_server.models import ReflectionResult
from .triggers import (
    ReflectionTrigger,
    ReflectionContext,
    ImportanceThresholdTrigger,
)
from .base import AbstractReflector

if TYPE_CHECKING:
    from persona.memory_structures.scratch import Scratch
    from persona.memory_structures.associative_memory import AssociativeMemory
    from persona.cognitive_modules.retriever.base import AbstractRetriever
    from reverie.backend_server.models import AgentContext


class LegacyReflector(AbstractReflector):
    """
    Legacy implementation of the Reflection cognitive module.
    
    Generates insights from accumulated experiences and conversations.
    Supports both scratch-based and contract-based interfaces.
    
    Now supports pluggable trigger strategies for experimental flexibility:
        reflector = LegacyReflector(scratch, retriever)
        reflector.trigger_strategy = TimedTrigger(interval_minutes=60)
    """
    
    def __init__(self, 
                 scratch: "Scratch", 
                 retriever: "AbstractRetriever",
                 trigger_strategy: Optional[ReflectionTrigger] = None):
        """
        Args:
            scratch: Scratch state for legacy compatibility.
            retriever: Retriever module for memory retrieval.
            trigger_strategy: Optional custom trigger strategy.
                              Defaults to ImportanceThresholdTrigger (original paper).
        """
        self.scratch = scratch
        self.retriever = retriever
        self.trigger_strategy = trigger_strategy or ImportanceThresholdTrigger()

    def reflect(self,
                agent: Optional["AgentContext"] = None,
                memory_store: Optional["AssociativeMemory"] = None,
                retriever: Optional["AbstractRetriever"] = None
    ) -> "ReflectionResult":
        """
        Generate reflections from accumulated experiences.
        
        Supports both interfaces:
        - Legacy: reflect() - uses self.scratch and self.retriever
        - New: reflect(agent, memory_store, retriever) - explicit dependencies
        
        Returns:
            ReflectionResult with new thoughts and counter info (or None for legacy)
        """
        # Use provided or default dependencies
        a_mem = memory_store if memory_store else self.scratch.a_mem
        ret = retriever if retriever else self.retriever
        
        new_thoughts = []
        should_reset = False
        
        # Use the trigger strategy for experimental flexibility
        trigger_result = self._check_trigger(a_mem)
        
        if trigger_result.should_reflect: 
            new_thoughts = self._run_reflect(a_mem, ret)
            if trigger_result.reset_importance_counter:
                self._reset_reflection_counter()
            should_reset = trigger_result.reset_importance_counter

        # Handle conversation reflection
        if self.scratch.chatting_end_time: 
            if self.scratch.curr_time + datetime.timedelta(0,10) == self.scratch.chatting_end_time: 
                convo_thoughts = self._reflect_on_conversation_internal(a_mem)
                new_thoughts.extend(convo_thoughts)

        return ReflectionResult(
            new_thoughts=new_thoughts,
            focal_points=[],
            importance_accumulated=0,
            should_reset_counter=should_reset
        )

    def reflect_on_conversation(self,
                                 agent: "AgentContext",
                                 conversation: list,
                                 memory_store: "AssociativeMemory"
    ) -> "ReflectionResult":
        """
        Generate reflections specifically about a recent conversation.
        """
        thoughts = self._reflect_on_conversation_internal(memory_store, conversation)
        return ReflectionResult(
            new_thoughts=thoughts,
            focal_points=[],
            importance_accumulated=0,
            should_reset_counter=False
        )

    def _reflect_on_conversation_internal(self, 
                                          a_mem: "AssociativeMemory" = None,
                                          conversation: list = None) -> List:
        """
        Internal implementation of conversation reflection.
        """
        a_mem = a_mem if a_mem else self.scratch.a_mem
        chat = conversation if conversation else self.scratch.chat
        thoughts = []
        
        all_utt = ""
        if chat: 
            for row in chat:  
                all_utt += f"{row[0]}: {row[1]}\n"

        if not all_utt:
            return thoughts

        evidence = [a_mem.get_last_chat(self.scratch.chatting_with).node_id]

        planning_thought = self._generate_planning_thought_on_convo(all_utt)
        planning_thought = f"For {self.scratch.name}'s planning: {planning_thought}"

        created = self.scratch.curr_time
        expiration = self.scratch.curr_time + datetime.timedelta(days=30)
        s, p, o = self._generate_action_event_triple(planning_thought)
        keywords = set([s, p, o])
        thought_poignancy = self._generate_poig_score("thought", planning_thought)
        thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

        thought1 = a_mem.add_thought(created, expiration, s, p, o, 
                                    planning_thought, keywords, thought_poignancy, 
                                    thought_embedding_pair, evidence)
        thoughts.append(thought1)

        memo_thought = self._generate_memo_on_convo(all_utt)
        memo_thought = f"{self.scratch.name} {memo_thought}"

        created = self.scratch.curr_time
        expiration = self.scratch.curr_time + datetime.timedelta(days=30)
        s, p, o = self._generate_action_event_triple(memo_thought)
        keywords = set([s, p, o])
        thought_poignancy = self._generate_poig_score("thought", memo_thought)
        thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

        thought2 = a_mem.add_thought(created, expiration, s, p, o, 
                                    memo_thought, keywords, thought_poignancy, 
                                    thought_embedding_pair, evidence)
        thoughts.append(thought2)
        
        return thoughts

    def _check_trigger(self, a_mem: "AssociativeMemory" = None) -> "TriggerResult":
        """
        Check if reflection should be triggered using the configured strategy.
        
        Builds a ReflectionContext from scratch state and delegates to the strategy.
        """
        from .triggers import TriggerResult
        
        a_mem = a_mem if a_mem else self.scratch.a_mem
        
        context = ReflectionContext(
            importance_trigger_max=self.scratch.importance_trigger_max,
            importance_trigger_curr=self.scratch.importance_trigger_curr,
            importance_accumulated=self.scratch.importance_ele_n,
            current_time=self.scratch.curr_time,
            last_reflection_time=None,  # TODO: Track this in scratch if needed
            total_events=len(a_mem.seq_event) if a_mem else 0,
            total_thoughts=len(a_mem.seq_thought) if a_mem else 0,
            events_since_reflection=0,  # TODO: Track this if needed
            thoughts_since_reflection=0,  # TODO: Track this if needed
            has_memories=bool(a_mem and (a_mem.seq_event or a_mem.seq_thought)),
        )
        
        result = self.trigger_strategy.check(context)
        
        # Log for debugging (maintaining original behavior)
        print(self.scratch.name, "persona.scratch.importance_trigger_curr::", self.scratch.importance_trigger_curr)
        print(self.scratch.importance_trigger_max)
        print(f"Trigger result: {result.reason}")
        
        return result
    
    def _reflection_trigger(self): 
        """Deprecated: Use _check_trigger with trigger_strategy instead."""
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

    def _run_reflect(self, 
                     a_mem: "AssociativeMemory" = None,
                     retriever: "AbstractRetriever" = None) -> List:
        """
        Run the reflection process and return new thoughts.
        """
        a_mem = a_mem if a_mem else self.scratch.a_mem
        retriever = retriever if retriever else self.retriever
        new_thoughts = []
        
        # Reflection requires certain focal points. Generate that first. 
        focal_points = self._generate_focal_points(3)
        # Retrieve the relevant Nodes object for each of the focal points. 
        retrieved = retriever.retrieve_weighted(focal_points)

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

                new_thought = a_mem.add_thought(created, expiration, s, p, o, 
                                            thought, keywords, thought_poignancy, 
                                            thought_embedding_pair, evidence)
                new_thoughts.append(new_thought)
        
        return new_thoughts

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
