import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import requests

def download_api_single(
        api_name: str,
        endpoint: str) -> dict:
    """Download a single file via the Archipelago Web API
    Args:
            api_name: Name of the API. Also used for the output filename
            endpoint: Endpoint to query
            output_folder: Folder to write the downloaded file to
    Returns:
            The downloaded file as a json dict
    """
    print(f"Downloading {api_name}")
    data = requests.get(f"https://archipelago.gg/api/{endpoint}").json()
    return data

# TODO - Cache datapackage files to their own files and check for existence before downloading
# See %LOCALAPPDATA%\Archipelago\Cache for how this could be done
# Should we always just download them? Probably unless we know they aren't corrupted
def download_room_datapackages(
        api_name: str,
        static_tracker: dict) -> dict:
    """Download multiple datapackages via the Archipelago Web API
    Args:
            api_name: Name of the API. Also used for the output filename
            static_tracker: dict from the static_tracker endpoint
            output_folder: Folder to write the downloaded file to
    Returns:
            The downloaded file as a json dict
    """
    print(f"Downloading {api_name}")
    data = {
        game: requests.get(f"https://archipelago.gg/api/datapackage/{static_tracker["datapackage"][game]["checksum"]}").json()
        for game in static_tracker["datapackage"]
    }
    return data

# Parse arguments
parser = argparse.ArgumentParser(description="Downloads data from an Archipelago room")
parser.add_argument("-r", "--room-suuid", type=str, required=True, help="Room SUUID. This is a string found in your room's URL. Example: https://archipelago.gg/<ROOM_SUUID>")
parser.add_argument("-f", "--output-folder", type=str, required=True, help="Output folder. This is where all json files and graphs will be written")
parser.add_argument("-d", "--debug", default=False, action="store_true", help="Print debug files")
args = parser.parse_args()

debug: bool = args.debug

# Create output folder and get the current time
output_folder = f"{args.output_folder}"
Path(output_folder).mkdir(parents=True, exist_ok=True)
now_time = datetime.now(tz=timezone.utc)

# Verify the time the data was last fetched so that we don't request data too quickly
cache_timeout_s = 1800
if Path(f"{output_folder}/last_fetched.json").exists():
    with open(f"{output_folder}/last_fetched.json", "r") as s:
        last_fetched = json.load(s)
    if "last_fetched" in last_fetched:
        old_time = datetime.strptime(last_fetched["last_fetched"], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        if (now_time - old_time).seconds <= cache_timeout_s:
            print(f"Data was last downloaded {(now_time - old_time).seconds} seconds ago which is less than the {cache_timeout_s} second ({cache_timeout_s/60} minute) cache timer. Not downloading room data")
            exit(0)

print(f"Using room-suuid={args.room_suuid}")

# /room_status/<suuid:room_id> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#room_statussuuidroom_id
# Cache timer: None
room_status = download_api_single(
    api_name="room_status",
    endpoint=f"/room_status/{args.room_suuid}")
tracker_suuid = room_status["tracker"]

# /tracker/<suuid:tracker> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#trackersuuidtracker
# Cache timer: 60 seconds
tracker = download_api_single(
    api_name="tracker",
    endpoint=f"/tracker/{tracker_suuid}")

# /static_tracker/<suuid:tracker> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#static_trackersuuidtracker
# Cache timer: 300 seconds
static_tracker = download_api_single(
    api_name="static_tracker",
    endpoint=f"/static_tracker/{tracker_suuid}")

# TODO - do we care about this for anything?
# /slot_data_tracker/<suuid:tracker> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#slot_data_trackersuuidtracker
# Cache timer: 300 seconds
slot_data_tracker = download_api_single(
    api_name="slot_data_tracker",
    endpoint=f"/slot_data_tracker/{tracker_suuid}")

# /datapackage/<string:checksum> - https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/webhost%20api.md#datapackagestringchecksum
# Cache timer: None
room_datapackages = download_room_datapackages(
    api_name="room_datapackages",
    static_tracker=static_tracker)

# Write the data to file
with open(f"{output_folder}/room_status.json", "w") as file:
    json.dump(room_status, file)
    print(f"Wrote room_status to {output_folder}/room_status.json")
with open(f"{output_folder}/tracker.json", "w") as file:
    json.dump(tracker, file)
    print(f"Wrote tracker to {output_folder}/tracker.json")
with open(f"{output_folder}/static_tracker.json", "w") as file:
    json.dump(static_tracker, file)
    print(f"Wrote static_tracker to {output_folder}/static_tracker.json")
with open(f"{output_folder}/slot_data_tracker.json", "w") as file:
    json.dump(slot_data_tracker, file)
    print(f"Wrote slot_data_tracker to {output_folder}/slot_data_tracker.json")
with open(f"{output_folder}/room_datapackages.json", "w") as file:
    json.dump(room_datapackages, file)
    print(f"Wrote room_datapackages to {output_folder}/room_datapackages.json")
last_fetched_json = {"last_fetched":datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")}
with open(f"{output_folder}/last_fetched.json", "w") as file:
    json.dump(last_fetched_json, file)
    print(f"Wrote last_fetched to {output_folder}/last_fetched.json")

if debug:
    indent = 3
    Path(f"{output_folder}/get-room-data-debug").mkdir(parents=True, exist_ok=True)

    print(f"\nWriting debug files to {output_folder}/get-room-data-debug")
    with open(f"{output_folder}/get-room-data-debug/room_status.json", "w") as file:
        json.dump(room_status, file, indent=indent)
        print(f"Wrote room_status to {output_folder}/get-room-data-debug/room_status.json")
    with open(f"{output_folder}/get-room-data-debug/tracker.json", "w") as file:
        json.dump(tracker, file, indent=indent)
        print(f"Wrote tracker to {output_folder}/get-room-data-debug/tracker.json")
    with open(f"{output_folder}/get-room-data-debug/static_tracker.json", "w") as file:
        json.dump(static_tracker, file, indent=indent)
        print(f"Wrote static_tracker to {output_folder}/get-room-data-debug/static_tracker.json")
    with open(f"{output_folder}/get-room-data-debug/slot_data_tracker.json", "w") as file:
        json.dump(slot_data_tracker, file, indent=indent)
        print(f"Wrote slot_data_tracker to {output_folder}/get-room-data-debug/slot_data_tracker.json")
    with open(f"{output_folder}/get-room-data-debug/room_datapackages.json", "w") as file:
        json.dump(room_datapackages, file, indent=indent)
        print(f"Wrote room_datapackages to {output_folder}/get-room-data-debug/room_datapackages.json")
    with open(f"{output_folder}/get-room-data-debug/last_fetched.json", "w") as file:
        json.dump(last_fetched_json, file, indent=indent)
        print(f"Wrote last_fetched to {output_folder}/get-room-data-debug/last_fetched.json")