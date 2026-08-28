import argparse
import graphviz
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Make a hint graph a room's data")
parser.add_argument("-f", "--data-folder", type=str, required=True, help="Folder containing room data retrieved by get-room-data.py")
parser.add_argument("-o", "--output-filename", type=str, help="Partial output filename for the graph. Data fetch date and extension are appended. Example: <output-filename>_<fetch-date>.png")
args = parser.parse_args()

# TODO - Make these configurable. Allow searching by slot name and alias too
node_id = 96 # GhostlyCrystal in Questionable Decisions
show_parent_nodes = True
show_child_nodes = False

# TODO - Filter out nodes with >= some number of hints to find - Make this configurable
high_hint_count = 2147483647

data_folder = args.data_folder
with open(f"{data_folder}/last_fetched.json", "r") as s:
   last_fetched = json.load(s)
with open(f"{data_folder}/room_status.json", "r") as file:
   room_status = json.load(file)
with open(f"{data_folder}/tracker.json", "r") as file:
   tracker = json.load(file)
with open(f"{data_folder}/static_tracker.json", "r") as file:
   static_tracker = json.load(file)
with open(f"{data_folder}/room_datapackages.json", "r") as file:
   room_datapackages = json.load(file)

fetch_time = last_fetched["last_fetched"]
output_filename = Path(f"{args.output_filename}_{fetch_time}")

# Flatten all the tracker["hints"][idx]["hints"] into a single list of dicts while getting rid of dupes
# https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint
finding_player_count = [0] * (len(static_tracker["player_game"]) + len(static_tracker["groups"]))
hints_raw = []
for hint_dict in tracker["hints"]:
   for hint in hint_dict["hints"]:
      if hint not in hints_raw:
         hints_raw.append(hint)
         # TODO - TEMPORARY - use to count how many unfound progression hints a slot has been hinted to find
         if hint[4] == False and (hint[6] & 0x1 == 1):
            finding_player_count[hint[1]-1] += 1

hints_raw = [
   {
      "receiving_player": hint[0], # int
      "finding_player": hint[1],   # int
      "location": hint[2],         # int
      "item": hint[3],             # int
      "found": hint[4],            # bool
      "entrance": hint[5],         # str = ""
      "item_flags": hint[6],       # int = 0
      "status": hint[7]            # HintStatus = HintStatus.HINT_UNSPECIFIED
   }
   for hint in hints_raw
]
with open(f"{data_folder}/hints_raw_unique.json", "w") as file:
   json.dump(hints_raw, file, indent=3)

high_hint_count_slots = [index + 1 for index, value in enumerate(finding_player_count) if value >= high_hint_count]

# Create an initial list of hints_processed
print("Processing hint data")
hints_processed = [
   {
      "player_num": tracker["aliases"][idx]["player"],
      "slot_name": slot_name[0],
      "game": slot_name[1],
      "alias": tracker["aliases"][idx]["alias"],
      "goal": tracker["player_status"][idx]["status"] == 30,
      "hints_to_find": [],
      "hints_for_others": [],
      "has_hint": False,
      "is_item_link": False
   }
   for (idx, slot_name) in enumerate(room_status["players"])
]

# Add item_links as their own slot
for item_link in static_tracker["groups"]:
   hints_processed.append({
      "player_num": item_link["slot"],
      "slot_name": item_link["name"],
      "game": hints_processed[item_link["members"][0]-1]["game"],
      "alias": None,
      "goal": False,
      "hints_to_find": [],
      "hints_for_others": [],
      "has_hint": False,
      "is_item_link": True
   })

# Set the pretty node names for later
for hint_datum in hints_processed:
   if hint_datum["alias"]:
      node_name = f"{hint_datum["alias"]} ({hint_datum["slot_name"]})"
   elif hint_datum["is_item_link"]:
      node_name = f"item_link: {hint_datum["slot_name"]}"
   else:
      node_name = f"{hint_datum["slot_name"]}"
   hint_datum["node_name"] = node_name
with open(f"{data_folder}/hints_processed_pre.json", "w") as file:
   json.dump(hints_processed, file, indent=3)

# Add hints to hints_processed
for hint in hints_raw:
   hints_to_find = []

   # Skip hints that were found
   if hint["found"] == True:
      continue

   # Skip non-progression hints
   if hint["item_flags"] & 0x1 != 1:
      continue

   if hint["finding_player"] in high_hint_count_slots:
      continue

   location = [k for k, v in room_datapackages[hints_processed[hint["finding_player"]-1]["game"]]["location_name_to_id"].items() if v == hint["location"]]
   item = [k for k, v in room_datapackages[hints_processed[hint["receiving_player"]-1]["game"]]["item_name_to_id"].items() if v == hint["item"]]

   hints_processed[hint["finding_player"]-1]["hints_to_find"].append({
      "finding_player": hint["finding_player"],
      "receiving_player": hint["receiving_player"],
      "location_id": hint["location"],
      "location_name": location[0],
      "item_id": hint["item"],
      "item_name": item[0],
   })
   hints_processed[hint["receiving_player"]-1]["hints_for_others"].append({
      "finding_player": hint["finding_player"],
      "receiving_player": hint["receiving_player"],
      "location_id": hint["location"],
      "location_name": location[0],
      "item_id": hint["item"],
      "item_name": item[0],
   })
   hints_processed[hint["receiving_player"]-1]["has_hint"] = True
   hints_processed[hint["finding_player"]-1]["has_hint"] = True
with open(f"{data_folder}/hints_processed.json", "w") as file:
   json.dump(hints_processed, file, indent=3)

visited_nodes: set = set()

# Show all nodes if we're not looking for a specific chain
if not show_child_nodes and not show_parent_nodes:
   visited_nodes.update([node["player_num"] for node in hints_processed])

# TODO - Do second pass to filter out nodes based on what node you wanna look at

if show_child_nodes:
   nodes: list = [hints_processed[node_id-1]]
   visited_nodes_child: set = set([hints_processed[node_id-1]["player_num"]]) # 1 based index into hints_processed
   while nodes:
      current_node = nodes.pop()
      for hint in current_node["hints_to_find"]:
         if hint["receiving_player"] not in visited_nodes_child:
            visited_nodes_child.add(hint["receiving_player"])
            nodes.append(hints_processed[hint["receiving_player"]-1])
   print(f"child_nodes=[{visited_nodes_child}]")
   visited_nodes.update(visited_nodes_child)

if show_parent_nodes:
   nodes: list = [hints_processed[node_id-1]]
   visited_nodes_parent: set = set([hints_processed[node_id-1]["player_num"]])
   while nodes:
      current_node = nodes.pop()
      for hint in current_node["hints_for_others"]:
         if hint["finding_player"] not in visited_nodes_parent:
            visited_nodes_parent.add(hint["finding_player"])
            nodes.append(hints_processed[hint["finding_player"]-1])
   print(f"parent_nodes=[{visited_nodes_parent}]")
   visited_nodes.update(visited_nodes_parent)

print(f"nodes_to_graph=[{visited_nodes}]")

# Create the graph
print("Creating hint graph")
dot = graphviz.Digraph('hint-graph', graph_attr={'rankdir':'LR'})

# Add all hints
for index in visited_nodes:
   player = hints_processed[index-1]
   if player["has_hint"]:
      dot.node(f"{player["player_num"]}", player["node_name"])
      for hint in player["hints_to_find"]:
         if hint["finding_player"] in visited_nodes and hint["receiving_player"] in visited_nodes:
            dot.edge(tail_name=f"{hint["finding_player"]}",
                     head_name=f"{hint["receiving_player"]}",
                     label=f"{hint["item_name"]} at {hint["location_name"]}")

# Save it!
# engines = ['dot','neato','fdp','sfdp','circo','twopi','osage','patchwork']
engines = ['dot']
for engine in engines:
   dot.engine = engine
   print(f"Saving to {data_folder}/graphs/{output_filename}.jpg")
   dot.render(filename=f"{output_filename}", directory=f"{data_folder}/graphs", format='jpg')
