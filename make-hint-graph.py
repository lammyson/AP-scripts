import argparse
import graphviz
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Make a hint graph of a room's hints. Graphs all hints by default.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
   "-f", "--data-folder",
   required=True,
   type=Path,
   metavar="FOLDER",
   help="Folder containing room data retrieved by get-room-data.py")
parser.add_argument(
   "-o", "--output-filename",
   metavar="FILE",
   help="Partial output filename for the graph. Data fetch date and extension are appended. Example: <output-filename>_<fetch-date>.png")
parser.add_argument(
   "-d", "--debug",
   default=False,
   action="store_true",
   help="Print debug"
)

slot_select_group = parser.add_argument_group(
   "Slot name options",
   description=
"""Use these arguments to select a specific slot/alias.
Used to highlight a specific slot red.
When combined with a hint mode option, it will be the slot that the hint chain is centered around."""
      ).add_mutually_exclusive_group(required=False)
slot_select_group.add_argument(
   "--slot-name",
   metavar="NAME",
   help="Slot name")
slot_select_group.add_argument(
   "--alias",
   help="Alias of the slot")
slot_select_group.add_argument(
   "--slot-id",
   type=int,
   metavar="ID",
   help="Id (integer) of the slot. Can be found on the room page")

hint_chain_group = parser.add_argument_group(
   "Hint chain options",
   description=
"""Requires a slot name option.""")
hint_chain_group.add_argument(
   "--depth",
   metavar="DEPTH",
   type=int,
   help="Sets how deep in the hint chain to display in both directions"
)
hint_chain_group.add_argument(
   "--parent-depth",
   metavar="DEPTH",
   type=int,
   help="Sets how deep in the hint chain to display for slots that you depend on"
)
hint_chain_group.add_argument(
   "--child-depth",
   metavar="DEPTH",
   type=int,
   help="Sets how deep in the hint chain to display for slots that depend on you"
)

args = parser.parse_args()
debug=args.debug

if debug:
   print("Just after argument parsing")
   print(f"\tdata-folder={args.data_folder}")
   print(f"\toutput-filename={args.output_filename}")
   print(f"\tslot-name={args.slot_name}")
   print(f"\talias={args.alias}")
   print(f"\tslot-id={args.slot_id}")
   print(f"\tdepth={args.depth}")
   print(f"\tparent_depth={args.parent_depth}")
   print(f"\tchild_depth={args.parent_depth}")
   print("")

if not args.data_folder.exists():
   parser.error(f"Data folder={args.data_folder} does not exist")
if not Path(args.data_folder).is_dir():
   parser.error(f"Data folder={args.data_folder} is not a directory")

show_parent_nodes = False
show_child_nodes = False
parent_depth=2147483647
child_depth=2147483647

if args.depth:
   show_parent_nodes = True
   parent_depth=args.depth
   show_child_nodes = True
   child_depth=args.depth
if args.parent_depth:
   show_parent_nodes = True
   parent_depth=args.parent_depth
if args.child_depth:
   show_child_nodes = True
   child_depth=args.child_depth

no_depth_option = args.depth == None and args.parent_depth == None and args.child_depth == None
no_slot_name = args.slot_name == None and args.alias == None and args.slot_id == None
if no_depth_option and no_slot_name:
   parser.error("One of the arguments --slot-name|--alias|--slot-id is required when using --depth|--parent-depth|--child-depth")

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

# argparse only allows one of slot_id/slot_name/alias to be set so no need to re-validate that here

# Validate slot id if it was provided
# TODO - support item_links
slot_id = args.slot_id
if slot_id:
   if slot_id > len(room_status["players"]):
      parser.error(f"slot_id={slot_id} is greater than the number of players in the room ({len(room_status["players"])})")

# Validate slot name if it was provided
# TODO - support item_links
slot_name = args.slot_name
if slot_name:
   matches = [[idx, player] for idx, player in enumerate(room_status["players"]) if player[0] == slot_name]

   if len(matches) == 0:
      parser.error(f"slot_name={slot_name} not found. Please check your spelling")
   elif len(matches) >= 2:
      error_json = []
      for match in matches:
         error_json.append({
            "alias": tracker["aliases"][match[0]+1]["alias"],
            "player": match[0]+1,
            "slot_name": match[1][0]
         })
      parser.error(f"slot_name={slot_name} found multiple times. This should never happen. Run get-room-info.py to pull fresh data\n\t{error_json}")

   slot_id = matches[0][0]+1

# Validate alias if it was provided
alias = args.alias
if alias:
   matches = [name for name in tracker["aliases"] if name["alias"] == alias]

   if len(matches) == 0:
      parser.error(f"alias={alias} not found. Please check your spelling")
   elif len(matches) >= 2: # aliases are not globally unique
      matches = [{k: v for k, v in d.items() if k != "team"} for d in matches]
      for match in matches:
         match["slot_name"] = room_status["players"][match["player"]-1][0]
      parser.error(f"alias={alias} found multiple times.\n\t{matches}")

   slot_id = matches[0]["player"]

# Create output filename
fetch_time = last_fetched["last_fetched"]
if args.output_filename != None:
   output_filename = Path(f"{args.output_filename}_{fetch_time}")
else:
   output_filename = Path(f"{fetch_time}")

if debug:
   print("Just after argument validation")
   print(f"\tdata-folder={data_folder}")
   print(f"\toutput-filename={output_filename}")
   print(f"\tslot-name={slot_name}")
   print(f"\talias={alias}")
   print(f"\tslot-id={slot_id}")
   print(f"\tshow_parent_nodes={show_parent_nodes}")
   print(f"\tparent_depth={parent_depth}")
   print(f"\tshow_child_nodes={show_child_nodes}")
   print(f"\tchild_depth={child_depth}")
   print("")

# Validation done. Tell the user what type of hint graph will be created
action_string = "Creating hint"
if not no_depth_option:
   action_string += f" chain for slot {room_status["players"][slot_id-1][0]} showing" # pyright: ignore[reportOptionalOperand]
   if show_parent_nodes and show_child_nodes:
      action_string += f" parent nodes at depth {parent_depth} and child nodes at depth {child_depth}"
   elif show_parent_nodes:
      action_string += f" parent nodes at depth {parent_depth}"
   elif show_child_nodes:
      action_string += f" child nodes at depth {child_depth}"
else:
   action_string += " graph for the entire multiworld"

print(action_string)

# Flatten all the tracker["hints"][idx]["hints"] into a single list of dicts while getting rid of dupes
# https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint
finding_player_count = [0] * (len(static_tracker["player_game"]) + len(static_tracker["groups"]))
hints_raw = []
for hint_dict in tracker["hints"]:
   for hint in hint_dict["hints"]:
      if hint not in hints_raw:
         hints_raw.append(hint)

         # Count how many unfound progression hints a slot has been hinted to find
         if hint[4] == False and (hint[6] & 0x1 == 1):
            finding_player_count[hint[1]-1] += 1
high_hint_count_slots = [index + 1 for index, value in enumerate(finding_player_count) if value >= high_hint_count]

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
if debug:
   with open(f"{data_folder}/hints_raw_unique.json", "w") as file:
      json.dump(hints_raw, file, indent=3)

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
if debug:
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
if debug:
   with open(f"{data_folder}/hints_processed.json", "w") as file:
      json.dump(hints_processed, file, indent=3)

visited_nodes: set = set()

# Show all nodes if we're not looking for a specific chain
if not show_child_nodes and not show_parent_nodes:
   visited_nodes.update([node["player_num"] for node in hints_processed])

# Show nodes that depend on us
if show_child_nodes:
   nodes: list = [hints_processed[slot_id-1]] # pyright: ignore[reportOptionalOperand]
   visited_nodes_child: set = set([hints_processed[slot_id-1]["player_num"]]) # pyright: ignore[reportOptionalOperand] # 1 based index into hints_processed
   while nodes and child_depth > 0:
      child_depth -= 1
      current_node = nodes.pop()
      for hint in current_node["hints_to_find"]:
         if hint["receiving_player"] not in visited_nodes_child:
            visited_nodes_child.add(hint["receiving_player"])
            nodes.append(hints_processed[hint["receiving_player"]-1])
   visited_nodes.update(visited_nodes_child)

# Show nodes that we depend on
if show_parent_nodes:
   nodes: list = [hints_processed[slot_id-1]] # pyright: ignore[reportOptionalOperand]
   visited_nodes_parent: set = set([hints_processed[slot_id-1]["player_num"]]) # pyright: ignore[reportOptionalOperand]
   while nodes and parent_depth > 0:
      parent_depth -= 1
      current_node = nodes.pop()
      for hint in current_node["hints_for_others"]:
         if hint["finding_player"] not in visited_nodes_parent:
            visited_nodes_parent.add(hint["finding_player"])
            nodes.append(hints_processed[hint["finding_player"]-1])
   visited_nodes.update(visited_nodes_parent)

# Create the graph
print("Creating hint graph")
dot = graphviz.Digraph('hint-graph', graph_attr={'rankdir':'LR'})

# If a specific slot was provided, color it red
if slot_id:
   dot.node(f"{hints_processed[slot_id-1]["player_num"]}", hints_processed[slot_id-1]["node_name"], color="red", fillcolor="red", style="filled", fontcolor="white")

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
