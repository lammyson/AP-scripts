#!/usr/bin/env python

import requests
import json

# Snivy Triggers
room_suuid = "E6WqOA-1T8-iemShH8cYyQ"
print(room_suuid)

# /room_status/<suuid:room_id> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#room_statussuuidroom_id
# Cache timer: None
# Some notable data
# - tracker - the tracker SUUID that can be used for other endpoints
# - players - slot name and game

# room_status = requests.get(f"https://archipelago.gg/api/room_status/{room_suuid}").json()
# with open("data/room_status.json", "w") as file:
#    json.dump(room_status, file, indent=3)
with open("data/room_status.json", "r") as s:
   room_status = json.load(s)

tracker_suuid = room_status["tracker"]
print(tracker_suuid)

# /tracker/<suuid:tracker> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#trackersuuidtracker
# Cache timer: 60 seconds
# Some notable data
# - aliases - dict of alias, player number, and team
# - hints

# tracker = requests.get(f"https://archipelago.gg/api/tracker/{tracker_suuid}").json()
# with open("data/tracker.json", "w") as file:
#    json.dump(tracker, file, indent=3)
with open("data/tracker.json", "r") as t:
   tracker = json.load(t)

# /static_tracker/<suuid:tracker> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#static_trackersuuidtracker
# Cache timer: 300 seconds
# Some notable data
# - datapackage checksums

# static_tracker = requests.get(f"https://archipelago.gg/api/static_tracker/{tracker_suuid}").json()
# with open("data/static_tracker.json", "w") as file:
#    json.dump(static_tracker, file, indent=3)
with open("data/static_tracker.json", "r") as s:
   static_tracker = json.load(s)

# /datapackage/<string:checksum> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#datapackagestringchecksum
# - Mapping into each game
# - Can probably jq all these together
room_datapackages = {
   game: requests.get(f"https://archipelago.gg/api/datapackage/{static_tracker["datapackage"][game]["checksum"]}").json()
   for game in static_tracker["datapackage"]
}
with open("data/room_datapackages.json", "w") as file:
   json.dump(room_datapackages, file, indent=3)

# static_tracker["datapackage"][idx]
# slots = {
#    slot[0]: {
#       "alias": tracker["aliases"][idx]["alias"],
#       "goal": tracker["player_status"][idx]["status"] == 30,
#    }
#    for (idx, slot) in enumerate(room_status["players"])
# }