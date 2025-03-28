import time
import requests
from datetime import datetime, timezone
from models import session, Profile, User, Room, Device, MinutelyConsumption
from data_proccessor import data_processor


def fetch_shelly_power(device_url):

    ## Try both Gen 2 (/rpc/Shelly.GetStatus) and Gen 1 (/status) Shelly APIs.
    ## Returns the power reading or None if unreachable.

    try:
        # Attempt Gen 2 (RPC)
        response = requests.get(f"{device_url}/rpc/Shelly.GetStatus", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("switch:0", {}).get("apower", 0.0)

        # If 404, attempt Gen 1
        if response.status_code == 404:
            response = requests.get(f"{device_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("meters", [{}])[0].get("power", 0.0)

        print(f"[fetch_shelly_power] Failed with status {response.status_code}")
    except requests.exceptions.RequestException as error:
        print(f"[fetch_shelly_power] Connection error: {error}")
        ## TODO: turn is_live to off if response isn't 200
        return None


def create_new_profile():

    ## Create a new Profile.
    ## If no User exists, create a new User first.

    existing_users = session.query(User).all()
    if not existing_users:
        print("No users found. Let's create one first.")
        user_name = input("Enter user name: ")
        user_email = input("Enter user email: ")
        user_password = input("Enter user password: ")
        new_user = User(user_name=user_name, email=user_email, password=user_password)
        session.add(new_user)
        session.commit()
        print(f"Created a new user named {user_name}")
        existing_users = [new_user]

    print("Choose a user for this profile:")
    for user in existing_users:
        print(f"  {user.user_id}: {user.user_name}")
    user_choice = input("Enter user ID or press Enter to pick the first: ").strip()
    chosen_user = None
    if user_choice:
        chosen_user = session.query(User).filter_by(user_id=user_choice).first()
    if not chosen_user:
        chosen_user = existing_users[0]

    profile_name = input("Enter profile name: ")
    new_profile = Profile(name=profile_name, user_id=chosen_user.user_id)
    session.add(new_profile)
    session.commit()
    print(f"Created new profile '{profile_name}' for user '{chosen_user.user_name}'")


def create_new_room():

    ## Create a new Room within an existing Profile.
    ## If no Profile exists, create one first.

    existing_profiles = session.query(Profile).all()
    if not existing_profiles:
        print("No profiles found. Please create a profile first.")
        return

    print("Choose a profile ID to add a room into (or press Enter for the first):")
    for profile in existing_profiles:
        print(f"  {profile.profile_id}: {profile.name}")
    profile_choice = input().strip()
    chosen_profile = None
    if profile_choice:
        chosen_profile = (
            session.query(Profile).filter_by(profile_id=profile_choice).first()
        )
    if not chosen_profile:
        chosen_profile = existing_profiles[0]

    room_name = input("Enter room name: ")
    new_room = Room(name=room_name, profile_id=chosen_profile.profile_id)
    session.add(new_room)
    session.commit()
    print(f"Created new room '{room_name}' under profile '{chosen_profile.name}'")


def check_device_url_valid(device_url):

    ## Quick connectivity check. If fetch_shelly_power returns None, it's invalid.

    test_power = fetch_shelly_power(device_url)
    return test_power is not None


def create_new_device():

    ## Create a new Device. Check connectivity (Gen1 / Gen2),
    ## then assign it to a chosen Profile & Room.

    device_url = input("Enter device URL (e.g. 'http://192.168.1.10'): ").strip()

    # Check if device already exists
    existing_device = session.query(Device).filter_by(device_url=device_url).first()
    if existing_device:
        print("A device with that URL already exists. Aborting.")
        return

    ## TODO: if setting device as is_live=false, then maybe this validation is redundant
    if not check_device_url_valid(device_url):
        print("Could not reach that Shelly device. Aborting.")
        return

    device_name = input("Enter device name: ").strip()
    device_type = input("Enter device type (e.g. TV/AC/Fridge): ").capitalize()

    # Choose profile
    profiles = session.query(Profile).all()
    if not profiles:
        print("No profiles exist. Creating a new profile first.")
        create_new_profile()
        profiles = session.query(Profile).all()
        if not profiles:
            print("Still no profiles, aborting device creation.")
            return

    print("Pick a profile to attach this device to:")
    for profile in profiles:
        print(f"  {profile.profile_id}: {profile.name}")
    profile_choice = input(
        "Enter profile ID or press Enter to pick the first: "
    ).strip()
    chosen_profile = None
    if profile_choice:
        chosen_profile = (
            session.query(Profile).filter_by(profile_id=profile_choice).first()
        )
    if not chosen_profile:
        chosen_profile = profiles[0]

    # Choose room
    if not chosen_profile.rooms:
        print(
            f"No rooms in profile '{chosen_profile.name}'. Creating a new one automatically."
        )
        room_name = input("Enter room name: ")
        new_room = Room(name=room_name, profile_id=chosen_profile.profile_id)
        session.add(new_room)
        session.commit()
        chosen_room = new_room
    else:
        print(f"Choose a room in profile '{chosen_profile.name}':")
        for room in chosen_profile.rooms:
            print(f"  {room.room_id}: {room.name}")
        room_choice = input("Enter room ID or press Enter to pick the first: ").strip()
        chosen_room = None
        if room_choice:
            chosen_room = session.query(Room).filter_by(room_id=room_choice).first()
        if not chosen_room:
            chosen_room = chosen_profile.rooms[0]

    new_device = Device(
        device_url=device_url,
        name=device_name,
        status="ON",
        type=device_type,
        room_id=chosen_room.room_id,
    )
    session.add(new_device)
    session.commit()

    print(
        f"Created new device '{device_name}' (URL: {device_url}) under profile '{chosen_profile.name}', room '{chosen_room.name}'"
    )


def show_menu():

    ## Show a menu of options:
    ##   1) New profile
    ##   2) New room
    ##   3) New device
    ##   4) Continue

    while True:
        print("\n--- Main Menu ---")
        print("1) Add new profile")
        print("2) Add new room")
        print("3) Add new device")
        print("4) Continue to data collection")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            create_new_profile()
        elif choice == "2":
            create_new_room()
        elif choice == "3":
            create_new_device()
        elif choice == "4":
            print("Continuing to data collection...")
            break
        else:
            print("Invalid choice. Please try again.")


def run_data_collector():

    ## Infinite loop for collecting data every minute.
    ## After each minute logs data, calls data_processor for aggregation.

    # Show menu first
    show_menu()

    print("Starting data collector. Press CTRL+C to stop at any time.")
    last_minute_logged = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    while True:
        current_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if current_minute > last_minute_logged:
            print(f"\n[Collector] Minute changed to {current_minute} (UTC)")
            devices_list = session.query(Device).all()
            for device in devices_list:
                if device.status == "ON":
                    power_value = fetch_shelly_power(device.device_url)
                    if power_value is not None:
                        log_entry = MinutelyConsumption(
                            device_id=device.device_id,
                            power_consumption=power_value,
                            time=current_minute,
                        )
                        session.add(log_entry)
                        print(
                            f"  => Logged {power_value}W for device '{device.name}' (ID: {device.device_id})"
                        )

            session.commit()
            data_processor()
            last_minute_logged = current_minute
        else:
            time.sleep(1)


if __name__ == "__main__":
    run_data_collector()
