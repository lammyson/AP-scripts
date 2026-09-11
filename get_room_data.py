import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import requests
from typing import Any

def __download_from_endpoint(
        api_name: str,
        endpoint: str) -> dict[str, Any]:
    """Download a single file via the Archipelago Web API
    Args:
            api_name: Name of the API
            endpoint: Endpoint to query
    Returns:
            The downloaded file as a json dict
    """
    print(f"Downloading {api_name}")
    data = requests.get(f"https://archipelago.gg/api/{endpoint}").json()
    return data

def get_file_safe_name(name: str) -> str:
    return "".join(c for c in name if c not in '<>:"/\\|?*')


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Downloads data from an Archipelago room")
    parser.add_argument(
        "-r", "--room-suuid",
        type=str,
        required=True,
        help="Room SUUID. This is a string found in your room's URL. Example: https://archipelago.gg/<ROOM_SUUID>")
    parser.add_argument(
        "-f", "--output-folder",
        type=str,
        required=True,
        help="Output folder. This is where all json files and graphs will be written")
    args = parser.parse_args()

    # Create output folder and get the current time
    output_folder: str = f"{args.output_folder}"
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    Path(".datapackages").mkdir(parents=True, exist_ok=True)
    now_time = datetime.now(tz=timezone.utc)

    # Verify the time the data was last fetched so that we don't request data too quickly
    cache_timeout_s = 1800
    if Path(f"{output_folder}/last_fetched.json").is_file():
        with open(f"{output_folder}/last_fetched.json", "r") as s:
            last_fetched = json.load(s)
        if "last_fetched" in last_fetched:
            old_time = datetime.strptime(last_fetched["last_fetched"], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            if (now_time - old_time).seconds <= cache_timeout_s:
                print(f"Data was last downloaded {(now_time - old_time).seconds} seconds ago which is less than the {cache_timeout_s} second ({cache_timeout_s/60:g} minute) cache timer. Not downloading room data")
                exit(0)

    print(f"Using room-suuid={args.room_suuid}")

    # /room_status/<suuid:room_id>
    # Cache timer: None
    room_status = __download_from_endpoint(
        api_name="room_status",
        endpoint=f"/room_status/{args.room_suuid}")
    tracker_suuid = room_status["tracker"]

    # /tracker/<suuid:tracker>
    # Cache timer: 60 seconds
    tracker = __download_from_endpoint(
        api_name="tracker",
        endpoint=f"/tracker/{tracker_suuid}")

    # /static_tracker/<suuid:tracker>
    # Cache timer: 300 seconds
    static_tracker = __download_from_endpoint(
        api_name="static_tracker",
        endpoint=f"/static_tracker/{tracker_suuid}")

    # /slot_data_tracker/<suuid:tracker>
    # Cache timer: 300 seconds
    slot_data_tracker = __download_from_endpoint(
        api_name="slot_data_tracker",
        endpoint=f"/slot_data_tracker/{tracker_suuid}")

    # /datapackage/<string:checksum>
    # Cache timer: None
    datapackages: list[dict[str, dict[str, Any]]] = []
    for game, data in static_tracker["datapackage"].items():
        safe_game_name: str = get_file_safe_name(game)
        if not Path(f".datapackages/{safe_game_name}/{data["checksum"]}.json").is_file():
            datapackages.append({game: __download_from_endpoint(
                api_name=f"datapackage {data["checksum"]} {game}",
                endpoint=f"datapackage/{data["checksum"]}")})
        else:
            print(f"Skipping download of datapackage {data["checksum"]} {game}")

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

    for datapackage in datapackages:
        game: str = next(iter(datapackage))
        safe_game_name: str = get_file_safe_name(game)
        checksum: str = get_file_safe_name(datapackage[game]["checksum"])
        Path(f".datapackages/{safe_game_name}").mkdir(parents=True, exist_ok=True)
        with open(f".datapackages/{safe_game_name}/{checksum}.json", "w") as file:
            json.dump(datapackage[game], file)
            print(f"Wrote {game} datapackage to .datapackages/{safe_game_name}/{checksum}.json")

    last_fetched_json = {"last_fetched": datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")}
    with open(f"{output_folder}/last_fetched.json", "w") as file:
        json.dump(last_fetched_json, file)
        print(f"Wrote last_fetched to {output_folder}/last_fetched.json")
