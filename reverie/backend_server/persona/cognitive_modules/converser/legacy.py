import datetime
import logging
from .base import AbstractConverser
from persona.prompt_template.run_gpt_prompt import *
from persona.prompt_template.gpt_structure import get_embedding

class LegacyConverser(AbstractConverser):
    def __init__(self, persona):
        self.persona = persona

    def open_session(self, convo_mode): 
        if convo_mode == "analysis": 
            curr_convo = []
            interlocutor_desc = "Interviewer"

            while True: 
                line = input("Enter Input: ")
                if line == "end_convo": 
                    break

                if int(run_gpt_generate_safety_score(self.persona, line)[0]) >= 8: 
                    print (f"{self.persona.scratch.name} is a computational agent, and as such, it may be inappropriate to attribute human agency to the agent in your communication.")        

                else: 
                    retrieved = self.persona.retriever.retrieve_weighted([line], 50)[line]
                    summarized_idea = self._generate_summarize_ideas(retrieved, line)
                    curr_convo += [[interlocutor_desc, line]]

                    next_line = self._generate_next_line(interlocutor_desc, curr_convo, summarized_idea)
                    curr_convo += [[self.persona.scratch.name, next_line]]


        elif convo_mode == "whisper": 
            whisper = input("Enter Input: ")
            self.receive_whisper(whisper)

    def receive_whisper(self, whisper):
        thought = self._generate_inner_thought(whisper)

        created = self.persona.scratch.curr_time
        expiration = self.persona.scratch.curr_time + datetime.timedelta(days=30)
        s, p, o = self._generate_action_event_triple(thought)
        keywords = set([s, p, o])
        thought_poignancy = self._generate_poig_score("event", whisper)
        thought_embedding_pair = (thought, get_embedding(thought))
        self.persona.a_mem.add_thought(created, expiration, s, p, o, 
                                thought, keywords, thought_poignancy, 
                                thought_embedding_pair, None)

    def chat(self, maze, target_persona): 
        curr_chat = []
        print ("July 23")

        for i in range(8): 
            focal_points = [f"{target_persona.scratch.name}"]
            retrieved = self.persona.retriever.retrieve_weighted(focal_points, 50)
            relationship = self._generate_summarize_agent_relationship(self.persona, target_persona, retrieved)
            print ("-------- relationshopadsjfhkalsdjf", relationship)
            last_chat = ""
            for i in curr_chat[-4:]:
                last_chat += ": ".join(i) + "\n"
            if last_chat: 
                focal_points = [f"{relationship}", 
                                f"{target_persona.scratch.name} is {target_persona.scratch.act_description}", 
                                last_chat]
            else: 
                focal_points = [f"{relationship}", 
                                f"{target_persona.scratch.name} is {target_persona.scratch.act_description}"]
            retrieved = self.persona.retriever.retrieve_weighted(focal_points, 15)
            utt, end = self._generate_one_utterance(maze, self.persona, target_persona, retrieved, curr_chat)

            curr_chat += [[self.persona.scratch.name, utt]]
            if end:
                break


            focal_points = [f"{self.persona.scratch.name}"]
            retrieved = target_persona.retriever.retrieve_weighted(focal_points, 50)
            relationship = self._generate_summarize_agent_relationship(target_persona, self.persona, retrieved)
            print ("-------- relationshopadsjfhkalsdjf", relationship)
            last_chat = ""
            for i in curr_chat[-4:]:
                last_chat += ": ".join(i) + "\n"
            if last_chat: 
                focal_points = [f"{relationship}", 
                                f"{self.persona.scratch.name} is {self.persona.scratch.act_description}", 
                                last_chat]
            else: 
                focal_points = [f"{relationship}", 
                                f"{self.persona.scratch.name} is {self.persona.scratch.act_description}"]
            retrieved = target_persona.retriever.retrieve_weighted(focal_points, 15)
            utt, end = self._generate_one_utterance(maze, target_persona, self.persona, retrieved, curr_chat)

            curr_chat += [[target_persona.scratch.name, utt]]
            if end:
                break

        print ("July 23 PU")
        for row in curr_chat: 
            print (row)
        print ("July 23 FIN")

        return curr_chat

    def _generate_summarize_ideas(self, nodes, question): 
        statements = ""
        for n in nodes:
            statements += f"{n.embedding_key}\n"
        summarized_idea = run_gpt_prompt_summarize_ideas(self.persona, statements, question)[0]
        return summarized_idea

    def _generate_next_line(self, interlocutor_desc, curr_convo, summarized_idea):
        # Original chat -- line by line generation 
        prev_convo = ""
        for row in curr_convo: 
            prev_convo += f'{row[0]}: {row[1]}\n'

        next_line = run_gpt_prompt_generate_next_convo_line(self.persona, 
                                                            interlocutor_desc, 
                                                            prev_convo, 
                                                            summarized_idea)[0]  
        return next_line

    def _generate_inner_thought(self, whisper):
        inner_thought = run_gpt_prompt_generate_whisper_inner_thought(self.persona, whisper)[0]
        return inner_thought

    def _generate_action_event_triple(self, act_desp): 
        logging.debug("GNS FUNCTION: <generate_action_event_triple>")
        return run_gpt_prompt_event_triple(act_desp, self.persona)[0]

    def _generate_poig_score(self, event_type, description): 
        logging.debug("GNS FUNCTION: <generate_poig_score>")

        if "is idle" in description: 
            return 1

        if event_type == "event" or event_type == "thought": 
            return run_gpt_prompt_event_poignancy(self.persona, description)[0]
        elif event_type == "chat": 
            return run_gpt_prompt_chat_poignancy(self.persona, 
                                self.persona.scratch.act_description)[0]

    def _generate_summarize_agent_relationship(self, init_persona, target_persona, retrieved): 
        all_embedding_keys = list()
        for key, val in retrieved.items(): 
            for i in val: 
                all_embedding_keys += [i.embedding_key]
        all_embedding_key_str =""
        for i in all_embedding_keys: 
            all_embedding_key_str += f"{i}\n"

        summarized_relationship = run_gpt_prompt_agent_chat_summarize_relationship(
                                    init_persona, target_persona,
                                    all_embedding_key_str)[0]
        return summarized_relationship

    def _generate_one_utterance(self, maze, init_persona, target_persona, retrieved, curr_chat): 
        # Chat version optimized for speed via batch generation
        curr_context = (f"{init_persona.scratch.name} " + 
                    f"was {init_persona.scratch.act_description} " + 
                    f"when {init_persona.scratch.name} " + 
                    f"saw {target_persona.scratch.name} " + 
                    f"in the middle of {target_persona.scratch.act_description}.\n")
        curr_context += (f"{init_persona.scratch.name} " +
                    f"is initiating a conversation with " +
                    f"{target_persona.scratch.name}.")

        print ("July 23 5")
        x = run_gpt_generate_iterative_chat_utt(maze, init_persona, target_persona, retrieved, curr_context, curr_chat)[0]

        print ("July 23 6")

        print ("adshfoa;khdf;fajslkfjald;sdfa HERE", x)

        return x["utterance"], x["end"]
