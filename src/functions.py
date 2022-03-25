import asyncio
import json
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import aiobungie
import aiocurl
import requests

from src.Settings import Settings

headers = {}


def get(endpoint: str):
    """
    Does a GET request to the Bungie API.

    :param endpoint: The endpoint, not the full URL.
    :return: The Bungie Response content.
    """
    _data = requests.get(
        "https://www.bungie.net/platform" + endpoint,
        headers=headers
    )

    if _data.status_code == 200:
        return _data.json()["Response"]

    raise BrokenPipeError(
        "GET request to " + endpoint + " yielded status code " + str(_data.status_code) + ": "
        + _data.text
    )


def post(endpoint: str, _data):
    """
    Does a GET request to the Bungie API.

    :param endpoint: The endpoint, not the full URL.
    :param _data: The data to include in the request.
    :return: The Bungie Response content.
    """
    _data = requests.post(
        "https://www.bungie.net/platform" + endpoint,
        headers=headers,
        data=_data
    )

    if _data.status_code == 200:
        return _data.json()["Response"]

    raise BrokenPipeError(
        "POST request to " + endpoint + " yielded status code " + str(_data.status_code) + ": "
        + _data.text
    )


def get_clan_members_with_all_memberships(clan_id, skip):
    """
    Get a list of clan members, skipping over the given ID.

    :param clan_id: GroupId of the clan to use.
    :param skip: Primary membershipId of the player to skip.
    :return: A list of all player objects with all memberships.
    """

    filename = os.path.join(Settings.DataFolder, f"clanmembers_{clan_id}_without_{skip}.json")

    if not os.path.exists(filename) and not Settings.RequeryClanmates:
        sys.stdout.flush()
        sys.stderr.write('Error: Cannot read clan members from cache: File not found: ' + filename + "\n")
        exit(1)

    requery = Settings.RequeryClanmates

    if requery:
        clan_details = get(f"/GroupV2/{clan_id}/")
        print("Loading clan member details for " + clan_details["detail"]["name"])

        clan_members = get(f"/GroupV2/{clan_id}/Members/")

        _data = []

        for member in clan_members["results"]:
            member_id = member["destinyUserInfo"]["membershipId"]
            member_type = member["destinyUserInfo"]["membershipType"]

            if str(member_id) == skip:
                print("Skipping " + str(member_id) + "...")
                continue

            print("Requesting data of clanmember ID " + str(member_id))

            profile = get(
                "/Destiny2/{membershipType}/Profile/{membershipId}/LinkedProfiles/?getAllMemberships=true"
                    .format(membershipType=member_type, membershipId=member_id)
            )

            _data.append(profile)

        with open(filename, "w") as f:
            json.dump(_data, f)
            print('Saved clan member details to ' + filename)

    with open(filename, "r") as f:
        print('Read clan member details from ' + filename)
        return json.load(f)


def get_activity_date(activity_id) -> str:
    """
    Gets the date of an activity in ISO format

    :param activity_id: The activity ID, as number or string.
    :return: The date, in ISO format
    """
    data = get("/Destiny2/Stats/PostGameCarnageReport/{}/".format(activity_id))
    return data["period"]


def iso_to_nice_iso(date_str: str) -> str:
    """
    datetime.fromisoformat() doesn"t like the "Z" timezone, so we convert it to "+00:00"

    :param date_str: The date ending in Z
    :return: The same date, ending in +00:00
    """
    return date_str[:len(date_str) - 1] + "+00:00"


def get_player():
    player_bungiename = Settings.BungieName

    [display_name, display_name_code] = player_bungiename.split("#", 2)

    player_object = {
        "displayName": display_name,
        "displayNameCode": display_name_code
    }

    profiles = post("/Destiny2/SearchDestinyPlayerByBungieName/-1/", json.dumps(player_object))

    membership_id = profiles[0]["membershipId"]
    membership_type = profiles[0]["membershipType"]

    return membership_id, membership_type, display_name


def get_activity_batches(player_id, player_membership, file_identifier: str) -> list:
    """
    Gets activities in sizes of 250 (the Bungie limit)

    :param file_identifier: The name to add to the filename
    :param player_id: The membership_id of the player.
    :param player_membership: The membership_type of the player.
    :return: A list of the batches in the format
    {
        "character": int, # character type
        "data": list,     # Bungie response
        "from": string,   # first date of the batch
        "to": string      # last date of the batch
    }
    """

    filename = os.path.join(Settings.DataFolder, f"activities_{file_identifier}.json")

    if not os.path.exists(filename) and not Settings.RequeryActivityBatches:
        sys.stdout.flush()
        sys.stderr.write('Error: Cannot read activity batches from cache: File not found: ' + filename + "\n")
        exit(1)

    requery = Settings.RequeryActivityBatches

    if requery:
        membership_id = player_id
        membership_type = player_membership

        account = get(
            "/Destiny2/{membershipType}/Profile/{destinyMembershipId}/?components=200".format(
                membershipType=membership_type,
                destinyMembershipId=membership_id
            )
        )

        _activities = []

        for character_id in account["characters"]["data"]:
            character_type = account["characters"]["data"][character_id]["classType"]
            character_name = aiobungie.Class(character_type).__str__()

            print("Requesting activities for character with ID " + str(character_id) + " (" + character_name + ")")

            for i in range(500):
                data = get(
                    "/Destiny2/{membershipType}/Account/{destinyMembershipId}/Character/{characterId}/Stats/Activities/?mode=0&count=250&page={page}"
                        .format(
                        membershipType=membership_type,
                        destinyMembershipId=membership_id,
                        characterId=character_id,
                        page=i
                    )
                )

                if "activities" not in data:
                    print("Loaded data for " + character_name + ", " + str(len(_activities)) + " batches total")
                    break

                _activities.append({
                    "character": character_type,
                    "data": data["activities"],
                    "from": iso_to_nice_iso(data["activities"][-1]["period"]),
                    "to": iso_to_nice_iso(data["activities"][0]["period"])
                })

                print("Requested " + character_name + " activity page " + str(i)
                      + ", ranging from " + data["activities"][-1]["period"]
                      + " to " + data["activities"][0]["period"])

        print("Loaded data for all characters.")

        with open(filename, "w") as f:
            json.dump(_activities, f)
            print('Saved activity batches to ' + filename)

    with open(filename, "r") as f:
        print('Read activity batches from ' + filename)
        return json.load(f)[::-1]


def filter_activities(batches: list) -> list:
    """
    Filters and flattens activity batches.

    :param batches: The list of batches.
    :return:
    """
    final_results = []
    indices_to_remove = []

    filters = Settings.Filters.getFilters()
    batch_amount = len(batches)

    print("Applying filters to batches...")

    for batch_index in range(batch_amount):
        batch = batches[batch_index]

        for filter_data in filters:
            filter_type = filter_data["type"]
            filter_op = filter_data["operator"]
            filter_value = filter_data["value"]

            if filter_type == "character":
                if filter_op == "is":
                    if batch["character"] != filter_value:
                        indices_to_remove.append(batch_index)
                        break

                if filter_op == "is not":
                    if batch["character"] == filter_value:
                        indices_to_remove.append(batch_index)
                        break

                if filter_op == "in":
                    if batch["character"] not in filter_value:
                        indices_to_remove.append(batch_index)
                        break

                if filter_op == "not in":
                    if batch["character"] in filter_value:
                        indices_to_remove.append(batch_index)
                        break

            if filter_type == "date":

                if filter_op == "before":
                    # if batch beginning is after set time
                    batch_from = datetime.fromisoformat(batch["from"])
                    value_before = datetime.fromisoformat(filter_value)

                    if batch_from > value_before:
                        indices_to_remove.append(batch_index)
                        break

                if filter_op == "after":
                    # if batch end is before set time
                    batch_to = datetime.fromisoformat(batch["to"])
                    value_after = datetime.fromisoformat(filter_value)

                    if batch_to < value_after:
                        indices_to_remove.append(batch_index)
                        break

    # remove marked batches
    batches = [element for i, element in enumerate(batches) if i not in indices_to_remove]

    print("Applying filters to single activities...")

    for batch in batches:
        indices_to_remove = []
        data = batch["data"]

        for i in range(len(data)):
            activity = data[i]

            for filter_data in filters:
                filter_type = filter_data["type"]
                filter_op = filter_data["operator"]
                filter_value = filter_data["value"]

                if filter_type == "date":
                    activity_date = datetime.fromisoformat(iso_to_nice_iso(activity["period"]))

                    if filter_op == "before":
                        # if batch beginning is after set time
                        value_before = datetime.fromisoformat(filter_value)

                        if activity_date > value_before:
                            indices_to_remove.append(i)
                            break

                    if filter_op == "after":
                        # if batch end is before set time
                        value_after = datetime.fromisoformat(filter_value)

                        if activity_date < value_after:
                            indices_to_remove.append(i)
                            continue

                if filter_type == "activity":
                    continue

                    # FIXME: this just filters out every single activity

                    # if filter_op == "is":
                    #     if filter_value not in activity["activityDetails"]["modes"]:
                    #         indices_to_remove.append(i)
                    #         break

                    # if filter_op == "in":
                    #     flag = 0
                    #     for filter_value_element in filter_value:
                    #         if filter_value_element in activity["activityDetails"]["modes"]:
                    #             flag = 1
                    #             break
                    #     if flag == 0:
                    #         indices_to_remove.append(i)
                    #         break

                    # if filter_op == "is not":
                    #     if filter_value in activity["activityDetails"]["modes"]:
                    #         indices_to_remove.append(i)
                    #         break

                    # if filter_op == "not in":
                    #     for filter_value_element in filter_value:
                    #         if filter_value_element in activity["activityDetails"]["modes"]:
                    #             indices_to_remove.append(i)
                    #             break

        # remove marked elements
        batch = [element for i, element in enumerate(data) if i not in indices_to_remove]

        final_results.extend(batch)

    print("Done applying filters.")

    return final_results


def print_batch_details(batches: list) -> None:
    """
    Prints the saved details of all batches in a list.

    :param batches: A list of activity batches.
    """
    for batch in batches:
        print(
            aiobungie.Class(batch["character"]).__str__() + " batch,"
            + " ranging from " + batch["from"]
            + " to " + batch["to"]
        )


def sort_activities_by_date(activities: list) -> list:
    """
    Sorts a list of activities by date using the "period" key.

    :param activities: The activities to sort.
    :return: The activities, sorted.
    """
    activities.sort(key=lambda x: datetime.fromisoformat(iso_to_nice_iso(x["period"])))
    return activities


async def request_activity_players(activity_id) -> list:
    """
    Does a single curl request for an activity. Throttles and delays if met with an error.

    :param activity_id: The activity ID to look up.
    :return: Array with two elements [data, blocking]. data is the response data, blocking is the amount of seconds
             Bungie wants us to throttle (usually 2)
    """

    handle = None
    try:
        handle = aiocurl.Curl()
    except aiocurl.error as e:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stderr.write("[ERROR] aiocurl.error: " + str(e) + "\n")
        sys.stderr.write("[ERROR] curl init failed - we likely ran out of connections to use" + "\n")
        sys.stderr.write("[ERROR] Exiting." + "\n")
        sys.stderr.flush()
        exit(1)

    handle.setopt(
        aiocurl.URL,
        "https://stats.bungie.net/Platform/Destiny2/Stats/PostGameCarnageReport/{}/".format(activity_id)
    )

    handle.setopt(
        aiocurl.HTTPHEADER,
        [
            "X-Api-Key: " + headers["X-Api-Key"],
            "Connection: close",
            "Accept: application/json"
        ]
    )

    handle.setopt(aiocurl.HTTP_VERSION, aiocurl.CURL_HTTP_VERSION_2_PRIOR_KNOWLEDGE)
    handle.setopt(aiocurl.SSL_VERIFYPEER, False)
    handle.setopt(aiocurl.FOLLOWLOCATION, True)
    if Settings.Advanced_CurlVerbose:
        handle.setopt(aiocurl.VERBOSE, True)

    data = BytesIO()
    handle.setopt(aiocurl.WRITEFUNCTION, data.write)

    flag = 0
    while flag == 0:
        try:
            await handle.perform()
            flag = 1
        except aiocurl.error:
            print("[WARN] curl threw error - waiting 30 seconds before proceeding")
            time.sleep(30)

    code = handle.getinfo(aiocurl.HTTP_CODE)

    handle.close()

    if str(code) == "200":
        data = json.loads(data.getvalue().decode("utf8"))
        blocking = data["ThrottleSeconds"]
        response = data["Response"]
        return [response, blocking]

    raise ConnectionError("Bungie API raised error: " + data.getvalue().decode("utf8"))


async def queue_activity_players(activities: list):
    """
    Queue an asyncio request for all the given activities.

    :param activities: A list of the activities to queue.
    :return: The combined results of the queries, in a list.
    """
    tasks = []
    for activity in activities:
        task = asyncio.create_task(request_activity_players(activity["activityDetails"]["instanceId"]))
        tasks.append(task)

    return await asyncio.gather(*tasks)


def chunk_and_get_activity_players(activities: list) -> list:
    """
    Chunks a list of activities and requests the details in chunks.

    :param activities: The list of activities.
    :return: A list of all the activity details.
    """
    length = len(activities)

    activity_details = []

    chunksize = Settings.Advanced_AsyncThreadAmount

    print("Requesting detailed PGCRs from Bungie, this can take a while...")

    for i in range(0, length, chunksize):
        data = asyncio.run(queue_activity_players(activities[i:i + chunksize]))

        for activity in data:
            [details, blocking] = activity

            activity_details.append(details)
            if blocking > 0:
                print("Sleeping {} seconds because Bungie told us to".format(blocking))
                time.sleep(blocking)
                print("Continuing.")

        print(
            "Requested players for " + str(i + chunksize) + " / " + str(length) + " activities ("
            + f"{((i + chunksize) * 100.0) / length:.2f}" + "%)"
        )

    print("Finished loading PGCRs.")

    return activity_details


def get_activity_details(activities: list,
                         file_identifier: str = 'unknown') -> list:
    """
    Gets the details of the given activities and saves them to file.

    :param file_identifier: The name to add to the filename
    :param activities: The list of activities to query.
    :return: The full list of the activity details, with all player IDs.
    """

    filename = os.path.join(Settings.DataFolder, f"players_{file_identifier}.json")

    if not os.path.exists(filename) and not Settings.RequeryActivityDetails:
        sys.stdout.flush()
        sys.stderr.write('Error: Cannot read activity details from cache: File not found: ' + filename + "\n")
        exit(1)

    requery = Settings.RequeryActivityDetails

    if requery:
        players = chunk_and_get_activity_players(activities)

        # Writing to sample.json
        with open(filename, "w") as f:
            json.dump(players, f)
        print('Saved activity details to ' + filename)

    with open(filename, "r") as f:
        print('Read activity details from ' + filename)
        return json.load(f)


def compare_against_clanmates(activities: list, clanmates: list) -> None:
    """
    Compare activity details against clanmate list.

    :param activities: The activity list, with player details.
    :param clanmates: The list of all clanmates, with all platforms.
    """

    print("Showing games with teammates...")

    counter = 0

    for activity in activities:
        for activity_player in activity["entries"]:
            for clanmate in clanmates:
                for clanmate_platform in clanmate["profiles"]:
                    activity_player_id = activity_player["player"]["destinyUserInfo"]["membershipId"]
                    clanmate_player_id = clanmate_platform["membershipId"]

                    if activity_player_id == clanmate_player_id:
                        player_name = clanmate_platform["displayName"]
                        activity_date = activity["period"]
                        activity_id = activity["activityDetails"]["instanceId"]

                        print("[" + activity_date + "] Activity " + str(activity_id) + " has clanmate " + player_name)

                        counter += 1
                        if Settings.OnlyListFirstN != 0 and counter >= Settings.OnlyListFirstN:
                            return


def run():
    Settings.validate()
    print('Data folder is ' + Settings.DataFolder)

    # https://github.com/tornadoweb/tornado/issues/2751#issuecomment-594460695
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # set specific values
    headers.update({"X-Api-Key": Settings.ApiKey})

    # make sure
    os.makedirs(Settings.DataFolder, exist_ok=True)

    player_id, player_membership, player_name = get_player()

    clan_members = get_clan_members_with_all_memberships(clan_id=Settings.ClanId,
                                                         skip=player_id)

    # get all activities
    activity_batches = get_activity_batches(player_id=player_id,
                                            player_membership=player_membership,
                                            file_identifier=player_name)

    # note that this filter will only reduce the calls to the Bungie API,
    # and will *not* work if you don't requery get_activity_details()!
    activities = filter_activities(batches=activity_batches)

    activities = sort_activities_by_date(activities=activities)

    # this is the costly request
    activities_with_players = get_activity_details(activities=activities,
                                                   file_identifier=player_name)

    # output results
    compare_against_clanmates(activities=activities_with_players,
                              clanmates=clan_members)
