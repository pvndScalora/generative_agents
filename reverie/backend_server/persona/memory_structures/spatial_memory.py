"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: spatial_memory.py
Description: Defines the MemoryTree class that serves as the agents' spatial
memory that aids in grounding their behavior in the game world. 
"""
import json
import sys
sys.path.append('../../')

from config import *
from global_methods import check_if_file_exists
from models import SpatialMemoryTree

class MemoryTree: 
  #Todo: use spatical memory as part of moving systems.
  def __init__(self, tree: SpatialMemoryTree): 
    """
    Initialize the MemoryTree with a spatial tree structure.

    The tree represents the hierarchy of the world:
    World -> Sector -> Arena -> [Game Objects]

    Example Tree:
    {
      "the Ville": {
        "Isabella's Apartment": {
          "Main Room": ["bed", "desk", "closet"],
          "Bathroom": ["shower", "sink", "toilet"]
        },
        "Hobbs Cafe": {
          "Cafe": ["counter", "table", "chair"]
        }
      }
    }
    """
    self.tree = tree


  def print_tree(self): 
    def _print_tree(tree, depth):
      dash = " >" * depth
      if type(tree) == type(list()): 
        if tree:
          print (dash, tree)
        return 

      for key, val in tree.items(): 
        if key: 
          print (dash, key)
        _print_tree(val, depth+1)
    
    _print_tree(self.tree, 0) 



  def get_str_accessible_sectors(self, curr_world): 
    """
    Returns a summary string of all the arenas that the persona can access 
    within the current sector. 

    Note that there are places a given persona cannot enter. This information
    is provided in the persona sheet. We account for this in this function. 

    INPUT
      None
    OUTPUT 
      A summary string of all the arenas that the persona can access. 
    EXAMPLE STR OUTPUT
      "bedroom, kitchen, dining room, office, bathroom"
    """
    try:
      x = ", ".join(list(self.tree[curr_world].keys()))
      return x
    except (KeyError, TypeError, AttributeError):
      return ""


  def get_str_accessible_sector_arenas(self, sector): 
    """
    Returns a summary string of all the arenas that the persona can access 
    within the current sector. 

    Note that there are places a given persona cannot enter. This information
    is provided in the persona sheet. We account for this in this function. 

    INPUT
      None
    OUTPUT 
      A summary string of all the arenas that the persona can access. 
    EXAMPLE STR OUTPUT
      "bedroom, kitchen, dining room, office, bathroom"
    """
    try:
      curr_world, curr_sector = sector.split(":")
      if not curr_sector: 
        return ""
      x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
      return x
    except (KeyError, ValueError, TypeError, AttributeError):
      return ""


  def get_str_accessible_arena_game_objects(self, arena):
    """
    Get a str list of all accessible game objects that are in the arena. If 
    temp_address is specified, we return the objects that are available in
    that arena, and if not, we return the objects that are in the arena our
    persona is currently in. 

    INPUT
      temp_address: optional arena address
    OUTPUT 
      str list of all accessible game objects in the gmae arena. 
    EXAMPLE STR OUTPUT
      "phone, charger, bed, nightstand"
    """
    curr_world, curr_sector, curr_arena = arena.split(":")

    if not curr_arena: 
      return ""

    try: 
      x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena]))
    except: 
      try:
        x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena.lower()]))
      except (KeyError, TypeError, AttributeError):
        # Arena doesn't exist in spatial memory - return empty string
        return ""
    return x


if __name__ == '__main__':
  x = f"../../../../environment/frontend_server/storage/the_ville_base_LinFamily/personas/Eddy Lin/bootstrap_memory/spatial_memory.json"
  x = MemoryTree(x)
  x.print_tree()

  print (x.get_str_accessible_sector_arenas("dolores double studio:double studio"))







