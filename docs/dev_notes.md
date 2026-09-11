# Dev Notes
## API endpoint info
Summarized to fit less space so I can see what each endpoint does at a glance
- https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md
- `room_status/<suuid:room_id>`
  - Cache timer: None
  - `downloads` - list of patch files
    - dict of patch file links, slot id
  - `last_activity` - timestamp of last room activity
  - `last_port` - current room port (could be inactive and need to be woken up)
  - `players` - list of players
    - list of slot name, game name
  - `timeout` - timeout of room in seconds
  - `tracker` - tracker suuid
- `tracker/<suuid:tracker>`
  - Cache timer: 60 seconds
  - `activity_timers` - list of each slot's last activity time
    - dict of slot id, team id, last activity time
  - `aliases` - list of alias data
    - dict of alias, slot id, team id
  - `connection_timers` - list of each slot's last connection time
    - dict of slot id, team id, last connection time
  - `hints` - list of hints per slot
    - dict of [hints](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint), slot id, team id
      - [hints](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint) are list of list of receiving_player (id), finding_player (id), location (id), item (id), found (bool), entrance (string), item flags (prog, useful, filler, trap), [HintStatus](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#hint)
  - `player_checks_done` - list of checks that have been completed
    - dict of locations (list of location ids), slot id, team id
  - `player_items_received` - list of items that have been received
    - dict of items (list of [NetworkItem](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#networkitem)), slot id, team id
      - [NetworkItem](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#networkitem) is item id, location id, finding slot id, flags (prog, useful, filler, trap)
  - `player_status` - list of player status
    - dict of slot id, [ClientStatus](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md#clientstatus), team id
      - ```python
        CLIENT_UNKNOWN = 0
        CLIENT_CONNECTED = 5
        CLIENT_READY = 10
        CLIENT_PLAYING = 20
        CLIENT_GOAL = 30
        ```
  - `total_checks_done` - checks done per team
- `static_tracker/<suuid:tracker>`
  - Cache timer: 300 seconds
  - `datapackage` - dict of game name and datapackage info
    - dict of checksum and version
  - `groups` - list of item link slot info
    - dict of slot ids in item_link (list), name, and slot id
  - `player_game` - list of games for each slot
    - dict of game name, slot id, team id
  - `player_locations_total` - list of total locations per slot
    - dict of slot id, team id, total locations
- `slot_data_tracker/<suuid:tracker>`
  - Cache timer: 300 seconds
  - list of dicts of slot id `players`, slot_data `slot_data`
    - slot_data is defined by the apworld
- `datapackages/<string:checksum>`
  - Cache timer: None
  - `checksum` - what it sounds like
  - `item_name_groups`- dict of item groups
    - dict of item group names to list of items in group
  - `item_name_to_id` - dict of item name to id
  - `location_name_groups` - dict of location groups
    - dict of location group names to list of locations in group
  - `location_name_to_id` - dict of location name to id
