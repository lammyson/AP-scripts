import argparse
import graphviz
import json

parser = argparse.ArgumentParser(description="Make a hint graph a room's data")
parser.add_argument("-f", "--data-folder", type=str, required=True, help="Folder containing room data retrieved by get-info.py")
args = parser.parse_args()

# TODO - make a hint graph for a certain slot only and dependent nodes and nodes it depends on

data_folder = args.data_folder
with open(f"{data_folder}/room_status.json", "r") as file:
   room_status = json.load(file)
with open(f"{data_folder}/tracker.json", "r") as file:
   tracker = json.load(file)
with open(f"{data_folder}/static_tracker.json", "r") as file:
   static_tracker = json.load(file)
with open(f"{data_folder}/room_datapackages.json", "r") as file:
   room_datapackages = json.load(file)

# Create an initial list of hint_data
print("Processing hint data")
hint_data = [
   {
      "player_num": tracker["aliases"][idx]["player"],
      "slot_name": slot_name[0],
      "game": slot_name[1],
      "alias": tracker["aliases"][idx]["alias"],
      "goal": tracker["player_status"][idx]["status"] == 30,
      "hints_to_find": [],
      "has_hint": False,
      "is_item_link": False
   }
   for (idx, slot_name) in enumerate(room_status["players"])
]

# Add item_links as their own slot
for item_link in static_tracker["groups"]:
   hint_data.append({
      "player_num": item_link["slot"],
      "slot_name": item_link["name"],
      "game": hint_data[item_link["members"][0]-1]["game"],
      "alias": None,
      "goal": False,
      "hints_to_find": [],
      "has_hint": False,
      "is_item_link": True
   })

# Set the pretty node names for later
for hint_datum in hint_data:
   if hint_datum["alias"]:
      node_name = f"{hint_datum["alias"]} ({hint_datum["slot_name"]})"
   elif hint_datum["is_item_link"]:
      node_name = f"item_link: {hint_datum["slot_name"]}"
   else:
      node_name = f"{hint_datum["slot_name"]}"
   hint_datum["node_name"] = node_name
with open(f"{data_folder}/hint_data_pre.json", "w") as file:
   json.dump(hint_data, file, indent=3)

# Flatten all the tracker["hints"][idx]["hints"] into a single list while getting rid of dupes
hints = []
for hint_dict in tracker["hints"]:
   for hint in hint_dict["hints"]:
      if hint not in hints:
         hints.append(hint)

# Add hints to hint_data
# https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint
for hint in hints:
   hints_to_find = []
   if hint[4] == False and (hint[6] & 0x1 == 1):
      location = [k for k, v in room_datapackages[hint_data[hint[1]-1]["game"]]["location_name_to_id"].items() if v == hint[2]]
      item = [k for k, v in room_datapackages[hint_data[hint[0]-1]["game"]]["item_name_to_id"].items() if v == hint[3]]

      hint_data[hint[1]-1]["hints_to_find"].append({
         "finding_player": hint[1],
         "receiving_player": hint[0],
         "location_id": hint[2],
         "location_name": location[0],
         "item_id": hint[3],
         "item_name": item[0],
      })
      hint_data[hint[0]-1]["has_hint"] = True
      hint_data[hint[1]-1]["has_hint"] = True
with open(f"{data_folder}/hint_data.json", "w") as file:
   json.dump(hint_data, file, indent=3)

# Create the graph
print("Creating hint graph")
dot = graphviz.Digraph('hint-graph', graph_attr={'rankdir':'LR'})

for player in hint_data:
   if player["has_hint"]:
      dot.node(f"{player["player_num"]}", player["node_name"])
      for hint in player["hints_to_find"]:
         dot.edge(tail_name=f"{hint["finding_player"]}",
                  head_name=f"{hint["receiving_player"]}",
                  label=f"{hint["item_name"]} at {hint["location_name"]}")

# Save it!
# engines = ['dot','neato','fdp','sfdp','circo','twopi','osage','patchwork']
engines = ['dot']
chain = 10
for engine in engines:
   dot.engine = engine
   dot = dot.unflatten(chain=chain)
   print(f"Saving to {data_folder}/graphs/{engine}.{chain}.gv.jpg")
   dot.render(filename=f"{engine}.{chain}.gv", directory=f"{data_folder}/graphs", format='jpg')

for engine in engines:
   dot.engine = engine
   print(f"Saving to {data_folder}/graphs/{engine}.gv.jpg")
   dot.render(filename=f"{engine}.gv", directory=f"{data_folder}/graphs", format='jpg')
