"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: associative_memory.py
Description: Defines the core long-term memory module for generative agents.

Note (May 1, 2023) -- this class is the Memory Stream module in the generative
agents paper. 
"""
import sys
sys.path.append('../../')

import json
import datetime
from models import Memory, MemoryType

class AssociativeMemory: 
  """
  The Memory Stream - core long-term memory module for generative agents.
  
  Stores three types of memories:
  - Events: Things that happened ("Isabella made coffee")
  - Thoughts: Reflections and insights ("I should invite more people to my party")
  - Chats: Conversations with other agents
  
  Attributes:
    kw_strength_event: Keyword frequency counter for events. Maps keyword -> count.
        NOTE: Currently tracked but NOT USED in cognitive decisions. This appears
        to be scaffolding for a feature that was never implemented (possibly for
        keyword-based reflection triggering via kw_strg_event_reflect_th).
    kw_strength_thought: Same as above but for thoughts.
  """
  
  def __init__(self, nodes_load=None, embeddings=None, kw_strength=None): 
    """
    Initialize AssociativeMemory.
    
    Args:
        nodes_load: Dict of node_id -> node_details to restore from disk. Default: empty.
        embeddings: Dict of embedding_key -> embedding_vector. Default: empty.
        kw_strength: Dict with 'kw_strength_event' and 'kw_strength_thought' keys.
                     Default: empty counters for both.
    """
    # Default arguments
    nodes_load = nodes_load or {}
    embeddings = embeddings or {}
    kw_strength = kw_strength or {"kw_strength_event": {}, "kw_strength_thought": {}}
    
    self.id_to_node = dict()

    self.seq_event = []
    self.seq_thought = []
    self.seq_chat = []

    self.kw_to_event = dict()
    self.kw_to_thought = dict()
    self.kw_to_chat = dict()

    # Keyword frequency counters (tracked but currently unused in decisions)
    self.kw_strength_event = dict()
    self.kw_strength_thought = dict()

    self.embeddings = embeddings

    for count in range(len(nodes_load.keys())): 
      node_id = f"node_{str(count+1)}"
      node_details = nodes_load[node_id]

      node_count = node_details["node_count"]
      type_count = node_details["type_count"]
      node_type = node_details["type"]
      depth = node_details["depth"]

      created = datetime.datetime.strptime(node_details["created"], 
                                           '%Y-%m-%d %H:%M:%S')
      expiration = None
      if node_details["expiration"]: 
        expiration = datetime.datetime.strptime(node_details["expiration"],
                                                '%Y-%m-%d %H:%M:%S')

      s = node_details["subject"]
      p = node_details["predicate"]
      o = node_details["object"]

      description = node_details["description"]
      embedding_pair = (node_details["embedding_key"], 
                        self.embeddings[node_details["embedding_key"]])
      poignancy =node_details["poignancy"]
      keywords = set(node_details["keywords"])
      filling = node_details["filling"]
      
      if node_type == "event": 
        self.add_event(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)
      elif node_type == "chat": 
        self.add_chat(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)
      elif node_type == "thought": 
        self.add_thought(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)

    if kw_strength["kw_strength_event"]: 
      self.kw_strength_event = kw_strength["kw_strength_event"]
    if kw_strength["kw_strength_thought"]: 
      self.kw_strength_thought = kw_strength["kw_strength_thought"]

    
  def get_state(self):
    r = dict()
    for count in range(len(self.id_to_node.keys()), 0, -1): 
      node_id = f"node_{str(count)}"
      node = self.id_to_node[node_id]

      r[node_id] = dict()
      r[node_id]["node_count"] = node.node_count
      r[node_id]["type_count"] = node.type_count
      r[node_id]["type"] = node.type.value if isinstance(node.type, MemoryType) else node.type
      r[node_id]["depth"] = node.depth

      r[node_id]["created"] = node.created.strftime('%Y-%m-%d %H:%M:%S')
      r[node_id]["expiration"] = None
      if node.expiration: 
        r[node_id]["expiration"] = (node.expiration
                                        .strftime('%Y-%m-%d %H:%M:%S'))

      r[node_id]["subject"] = node.subject
      r[node_id]["predicate"] = node.predicate
      r[node_id]["object"] = node.object

      r[node_id]["description"] = node.description
      r[node_id]["embedding_key"] = node.embedding_key
      r[node_id]["poignancy"] = node.poignancy
      r[node_id]["keywords"] = list(node.keywords)
      r[node_id]["filling"] = node.filling

    kw_strength = dict()
    kw_strength["kw_strength_event"] = self.kw_strength_event
    kw_strength["kw_strength_thought"] = self.kw_strength_thought
    
    return {
        "nodes": r,
        "kw_strength": kw_strength,
        "embeddings": self.embeddings
    }


  def add_event(self, created, expiration, s, p, o, 
                      description, keywords, poignancy, 
                      embedding_pair, filling):
    # Setting up the node ID and counts.
    node_count = len(self.id_to_node.keys()) + 1
    type_count = len(self.seq_event) + 1
    node_type = "event"
    node_id = f"node_{str(node_count)}"
    depth = 0

    # Node type specific clean up. 
    if "(" in description: 
      description = (" ".join(description.split()[:3]) 
                     + " " 
                     +  description.split("(")[-1][:-1])

    # Creating the <Memory> object.
    node = Memory(
        id=node_id,
        type=MemoryType.EVENT,
        description=description,
        created=created,
        last_accessed=created,
        subject=s,
        predicate=p,
        object=o,
        poignancy=poignancy,
        keywords=keywords,
        embedding_key=embedding_pair[0],
        filling=filling,
        expiration=expiration,
        depth=depth,
        node_count=node_count,
        type_count=type_count
    )

    # Creating various dictionary cache for fast access. 
    self.seq_event[0:0] = [node]
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      if kw in self.kw_to_event: 
        self.kw_to_event[kw][0:0] = [node]
      else: 
        self.kw_to_event[kw] = [node]
    self.id_to_node[node_id] = node 

    # Adding in the kw_strength
    if f"{p} {o}" != "is idle":  
      for kw in keywords: 
        if kw in self.kw_strength_event: 
          self.kw_strength_event[kw] += 1
        else: 
          self.kw_strength_event[kw] = 1

    self.embeddings[embedding_pair[0]] = embedding_pair[1]

    return node


  def add_thought(self, created, expiration, s, p, o, 
                        description, keywords, poignancy, 
                        embedding_pair, filling):
    # Setting up the node ID and counts.
    node_count = len(self.id_to_node.keys()) + 1
    type_count = len(self.seq_thought) + 1
    node_type = "thought"
    node_id = f"node_{str(node_count)}"
    depth = 1 
    try: 
      if filling: 
        depth += max([self.id_to_node[i].depth for i in filling])
    except: 
      pass

    # Creating the <Memory> object.
    node = Memory(
        id=node_id,
        type=MemoryType.THOUGHT,
        description=description,
        created=created,
        last_accessed=created,
        subject=s,
        predicate=p,
        object=o,
        poignancy=poignancy,
        keywords=keywords,
        embedding_key=embedding_pair[0],
        filling=filling,
        expiration=expiration,
        depth=depth,
        node_count=node_count,
        type_count=type_count
    )

    # Creating various dictionary cache for fast access. 
    self.seq_thought[0:0] = [node]
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      if kw in self.kw_to_thought: 
        self.kw_to_thought[kw][0:0] = [node]
      else: 
        self.kw_to_thought[kw] = [node]
    self.id_to_node[node_id] = node 

    # Adding in the kw_strength
    if f"{p} {o}" != "is idle":  
      for kw in keywords: 
        if kw in self.kw_strength_thought: 
          self.kw_strength_thought[kw] += 1
        else: 
          self.kw_strength_thought[kw] = 1

    self.embeddings[embedding_pair[0]] = embedding_pair[1]

    return node


  def add_chat(self, created, expiration, s, p, o, 
                     description, keywords, poignancy, 
                     embedding_pair, filling): 
    # Setting up the node ID and counts.
    node_count = len(self.id_to_node.keys()) + 1
    type_count = len(self.seq_chat) + 1
    node_type = "chat"
    node_id = f"node_{str(node_count)}"
    depth = 0

    # Creating the <Memory> object.
    node = Memory(
        id=node_id,
        type=MemoryType.CHAT,
        description=description,
        created=created,
        last_accessed=created,
        subject=s,
        predicate=p,
        object=o,
        poignancy=poignancy,
        keywords=keywords,
        embedding_key=embedding_pair[0],
        filling=filling,
        expiration=expiration,
        depth=depth,
        node_count=node_count,
        type_count=type_count
    )

    # Creating various dictionary cache for fast access. 
    self.seq_chat[0:0] = [node]
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      if kw in self.kw_to_chat: 
        self.kw_to_chat[kw][0:0] = [node]
      else: 
        self.kw_to_chat[kw] = [node]
    self.id_to_node[node_id] = node 

    self.embeddings[embedding_pair[0]] = embedding_pair[1]
        
    return node


  def get_summarized_latest_events(self, retention): 
    ret_set = set()
    for e_node in self.seq_event[:retention]: 
      ret_set.add(e_node.spo_summary())
    return ret_set


  def get_str_seq_events(self): 
    ret_str = ""
    for count, event in enumerate(self.seq_event): 
      ret_str += f'{"Event", len(self.seq_event) - count, ": ", event.spo_summary(), " -- ", event.description}\n'
    return ret_str


  def get_str_seq_thoughts(self): 
    ret_str = ""
    for count, event in enumerate(self.seq_thought): 
      ret_str += f'{"Thought", len(self.seq_thought) - count, ": ", event.spo_summary(), " -- ", event.description}'
    return ret_str


  def get_str_seq_chats(self): 
    ret_str = ""
    for count, event in enumerate(self.seq_chat): 
      ret_str += f"with {event.object.content} ({event.description})\n"
      ret_str += f'{event.created.strftime("%B %d, %Y, %H:%M:%S")}\n'
      for row in event.filling: 
        ret_str += f"{row[0]}: {row[1]}\n"
    return ret_str


  def retrieve_relevant_thoughts(self, s_content, p_content, o_content): 
    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_thought: 
        ret += self.kw_to_thought[i.lower()]

    ret = set(ret)
    return ret


  def retrieve_relevant_events(self, s_content, p_content, o_content): 
    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_event: 
        ret += self.kw_to_event[i]

    ret = set(ret)
    return ret


  def get_last_chat(self, target_persona_name): 
    if target_persona_name.lower() in self.kw_to_chat: 
      return self.kw_to_chat[target_persona_name.lower()][0]
    else: 
      return False



























