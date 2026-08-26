#!/usr/bin/env python
import graphviz
import json

with open("data/room_status.json", "r") as file:
   room_status = json.load(file)
with open("data/tracker.json", "r") as file:
   tracker = json.load(file)
with open("data/static_tracker.json", "r") as file:
   static_tracker = json.load(file)
with open("data/room_datapackages.json", "r") as file:
   room_datapackages = json.load(file)

# Create a json file with the data required to create the hint graph
# {
#    "player": int
#    "slot_name": str
#    "alias": str or null
#    "goal": bool
#    # Add a hint if found == false and item_flags has 0x1 set
#    "hints_to_find": { # tracker.json
#       "receiving_player": int
#       "finding_player": int
#       "location": int
#       "item": int
#       # "found": bool
#       # "entrance": str = ""
#       # "item_flags": int = 0 # 0x1 is progression
#       # "status": HintStatus = HintStatus.HINT_UNSPECIFIED
#    }
# }

# from typing import NamedTuple
# class Hint(NamedTuple):
#     receiving_player: int
#     finding_player: int
#     location: int
#     item: int
#     found: bool
#     entrance: str = ""
#     item_flags: int = 0
#     status: HintStatus = HintStatus.HINT_UNSPECIFIED

hint_data = [
   {
      "player_num": tracker["aliases"][idx]["player"],
      "slot_name": slot_name[0],
      "game": slot_name[1],
      "alias": tracker["aliases"][idx]["alias"],
      "goal": tracker["player_status"][idx]["status"] == 30,
      "hints_to_find": [],
   }
   for (idx, slot_name) in enumerate(room_status["players"])
]

# def find_keys(target_value, data):
#     stack = [data]
#     results = []
#     while stack:
#         current = stack.pop()
#         if isinstance(current, dict):
#             for k, v in current.items():
#                 if k == target_key:
#                     results.append(v)
#                 else:
#                     stack.append(v)
#         elif isinstance(current, list):
#             stack.extend(current)
#     return results

# receiving_player: 1,
# finding_player: 31,
# location: 1085039011, # Search the finding_player's locations
# item: 3626000, # Search the receiving player's items
# found: false,
# entrance: "",
# item_flags: 1,
# status: 0

for (idx, hint_datum) in enumerate(hint_data):
   if hint_datum["alias"]:
      node_name = f"{hint_datum["alias"]} ({hint_datum["slot_name"]})"
   else:
      node_name = f"{hint_datum["slot_name"]}"
   hint_datum["node_name"] = node_name

   hints_to_find = []
   for (idx2, hint) in enumerate(tracker["hints"][idx]["hints"]):
      if hint[4] == False and (hint[6] & 0x1 == 1) :
         location_names = []
         item_names = []
         location = [k for k, v in room_datapackages[hint_data[hint[1]-1]["game"]]["location_name_to_id"].items() if v == hint[2]]
         if location:
            location_names.extend(location)
         item = [k for k, v in room_datapackages[hint_data[hint[0]-1]["game"]]["item_name_to_id"].items() if v == hint[3]]
         if item:
            item_names.extend(item)

         hints_to_find.append({
            "finding_player": hint[1],
            "receiving_player": hint[0],
            "location_id": hint[2],
            "location_name": location_names,
            "item_id": hint[3],
            "item_name": item_names,
         })

   hint_data[idx]["hints_to_find"] = hints_to_find

with open("hint_data.json", "w") as file:
   json.dump(hint_data, file, indent=3)

# Setup the hint graph and render it
# save as the following formats: dot, jpg, json, pdf, png, svg
#
# Node name
# if alias == null:
#    <slot_name>
# else:
#    <alias> (<slot_name>) if alias is not
#
# Edges are <location_name> <item_name>
dot = graphviz.Digraph('hint-graph', comment='Hint Graph') 

# Create all nodes
for hint in hint_data:
   dot.node(f"{hint["player_num"]}", hint["node_name"])

# Then go make all the edges
for player in hint_data:
   for hint in player["hints_to_find"]:
      dot.edge(tail_name=f"{hint["finding_player"]}",
               head_name=f"{hint["receiving_player"]}",
               label=f"{hint["location_name"]}\n{hint["item_name"]}")

# Save it!
dot.render(format='dot')
dot.render(format='jpg')
dot.render(format='json')
dot.render(format='pdf')
dot.render(format='png')
dot.render(format='svg')