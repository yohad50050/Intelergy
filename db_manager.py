# db_manager.py

import sys
from sqlalchemy import text, Date
from datetime import datetime, timezone, timedelta

from models import (session,User,Profile,Room,Device,MinutelyConsumption,DeviceHourlyConsumption,DeviceDailyConsumption,DeviceWeeklyConsumption,HistoricalHourlyConsumption)

def ensure_profile_exists():
    
    #If no profiles exist, create one forcibly. Also ensures there's at least 1 user.
    
    all_profiles = session.query(Profile).all()
    if all_profiles:
        return None

    print("\nNo profiles found! Let's create a new profile.")
    all_users = session.query(User).all()
    if not all_users:
        print("No users exist. Let's create a new user first.")
        user_name = input("User name: ").strip()
        user_email = input("User email: ").strip()
        user_password = input("User password: ").strip()
        new_user = User(user_name=user_name, email=user_email, password=user_password)
        session.add(new_user)
        session.commit()
        print(f"Created user '{user_name}' (ID: {new_user.user_id})")
        chosen_user = new_user
    else:
        print("\nPick a user to assign this profile to:")
        for u in all_users:
            print(f"   - User ID: {u.user_id}, Name: '{u.user_name}'")
        chosen_uid = input("Enter User ID: ").strip()
        chosen_user = session.query(User).filter_by(user_id=chosen_uid).first()
        if not chosen_user:
            print(f"User ID '{chosen_uid}' not found. Aborting.")
            return None

    prof_name = input("Enter name for the new profile: ").strip()
    new_profile = Profile(name=prof_name, user_id=chosen_user.user_id)
    session.add(new_profile)
    session.commit()
    print(f"Created profile '{prof_name}' (ID: {new_profile.profile_id}) for user '{chosen_user.user_name}'")
    return new_profile

def ensure_room_exists(chosen_profile):
    
    #If the chosen profile has no rooms, forcibly create one.
    
    if not chosen_profile.rooms:
        print(f"\nProfile '{chosen_profile.name}' (ID: {chosen_profile.profile_id}) has no rooms. Creating one now.")
        room_name = input("Enter new room name: ").strip()
        new_room = Room(name=room_name, profile_id=chosen_profile.profile_id)
        session.add(new_room)
        session.commit()
        print(f"Created room '{room_name}' (ID: {new_room.room_id}) for profile '{chosen_profile.name}'")
        return new_room
    return None

def prompt_and_add_new_device(shelly_device_id):
    
    #If a device is missing, we create the profile/room if needed, then add the device.
    
    answer = input(f"No matching device found for '{shelly_device_id}'. Add this device? (yes/no): ").strip().lower()
    if answer not in ("yes", "y"):
        return

    newly_created_profile = ensure_profile_exists()
    all_profiles = session.query(Profile).all()
    if not all_profiles:
        print("No profiles available. Aborting device creation.")
        return

    print("\nSelect a profile (by ID) to add this device to:\n")
    for p in all_profiles:
        print(f"   - Profile ID: {p.profile_id}, Name: '{p.name}' (User ID: {p.user_id})")
    dev_profile_id = input("\nEnter Profile ID: ").strip()
    chosen_profile = session.query(Profile).filter_by(profile_id=dev_profile_id).first()
    if not chosen_profile:
        print(f"Profile ID '{dev_profile_id}' not found!")
        return

    new_room = ensure_room_exists(chosen_profile)
    chosen_profile = session.query(Profile).filter_by(profile_id=dev_profile_id).first()
    if not chosen_profile.rooms:
        print(f"No rooms found for profile ID {dev_profile_id}. Aborting.")
        return

    print("\nSelect a room (by ID) to add this device to:\n")
    for r in chosen_profile.rooms:
        print(f"   - Room ID: {r.room_id}, Name: '{r.name}'")
    dev_room_id = input("\nEnter Room ID: ").strip()
    chosen_room = session.query(Room).filter_by(room_id=dev_room_id).first()
    if not chosen_room:
        print(f"Room ID '{dev_room_id}' not found!")
        return

    dev_name = input("Enter device name (e.g., 'Living Room Plug'): ").strip()
    dev_type = input("Device type? (TV/AC/PC/Fridge, or leave blank): ").strip().capitalize()


    new_device = Device(device_url=shelly_device_id,name=dev_name,status="ON",type = type,room_id=chosen_room.room_id
)
    session.add(new_device)
    session.commit()
    print(f"Device '{dev_name}' (URL: {shelly_device_id}) added to Room '{chosen_room.name}', Profile '{chosen_profile.name}'.")

def update_device_status(device, amps):

    new_status = "ON" if amps > 0 else "OFF"
    if device.status != new_status:
        device.status = new_status
        session.commit()
        print(f"Updated device '{device.name}' (ID {device.device_id}) to '{new_status}' in DB.")
    else:
        print(f"Device '{device.name}' is already '{device.status}'.")

def clear_minutely_consumption():
    try:
        session.execute(text("DELETE FROM minutely_consumption"))
        session.commit()
        print("Cleared existing data in minutely_consumption table.")
    except Exception as e:
        session.rollback()
        print(f"Error clearing table: {e}")

def save_minutely_consumption(current_time, power_w, device_id):

    try:
        entry = MinutelyConsumption(
            time=current_time,
            power_consumption=int(power_w),
            device_id=device_id
        )
        session.add(entry)
        session.commit()
        print(f"Saved minutely record: {current_time}, Power: {power_w}W")
    except Exception as e:
        session.rollback()
        print(f"Error saving minutely consumption: {e}")
        sys.exit()

def compute_and_save_hourly_consumption(current_time, device_id):

    try:
        last_60 = (
            session.query(MinutelyConsumption.power_consumption)
            .filter_by(device_id=device_id)
            .order_by(MinutelyConsumption.time.desc())
            .limit(60)
            .all()
        )
        power = [row[0] for row in last_60]
        if len(power) == 3:
            avg_power = sum(power) / len(power)

            # 1) Save short-term hourly consumption
            hourly_entry = DeviceHourlyConsumption(
                time=current_time,
                hour_average_power=int(avg_power),
                device_id=device_id
            )
            session.add(hourly_entry)
            session.commit()
            print(f"Hourly average saved: {avg_power}W")

            # Save permanent historical consumption
            device_obj = session.query(Device).get(device_id)
            hist_entry = HistoricalHourlyConsumption(
                start_time=current_time,
                hour_average_power=int(avg_power)
            )
            hist_entry.devices.append(device_obj)  
            session.add(hist_entry)
            session.commit()
            print("Historical hourly usage saved permanently.")

            # Clear out minutely data
            session.query(MinutelyConsumption).filter_by(device_id=device_id).delete()
            session.commit()
            print("Minutely data cleared after hourly aggregation.")
            return avg_power
        else:
            print("Not enough minutely data for hourly calc.")
            return None
    except Exception as e:
        session.rollback()
        print(f"Error computing hourly consumption: {e}")
        sys.exit()

def compute_and_save_daily_consumption(current_date, device_id):
    try:
        rows = (session.query(DeviceHourlyConsumption.hour_average_power).filter(DeviceHourlyConsumption.device_id == device_id).filter(DeviceHourlyConsumption.time.cast(Date) == current_date).all())
        if rows:
            power = [r[0] for r in rows]
            daily_avg = sum(power) / len(power)
            daily_entry = DeviceDailyConsumption(date=current_date,daily_average=int(daily_avg),device_id=device_id)
            session.add(daily_entry)
            session.commit()
            print(f"Daily average saved: {daily_avg}W on {current_date}")

            session.query(DeviceHourlyConsumption).filter_by(device_id=device_id).delete()
            session.commit()
            print("Hourly data cleared after daily aggregation.")
            return daily_avg
        else:
            print("No hourly data for daily consumption.")
            return None
    except Exception as e:
        session.rollback()
        print(f"Error computing daily consumption: {e}")
        sys.exit()

def compute_and_save_weekly_consumption(current_date, device_id):
    try:
        week_start = current_date - timedelta(days=6)
        rows = (session.query(DeviceDailyConsumption.daily_average).filter(DeviceDailyConsumption.device_id == device_id).filter(DeviceDailyConsumption.date >= week_start).filter(DeviceDailyConsumption.date <= current_date).all())
        if rows:
            power = [r[0] for r in rows]
            weekly_avg = sum(power) / len(power)
            w_entry = DeviceWeeklyConsumption(date=current_date,weekly_average=int(weekly_avg),device_id=device_id)
            session.add(w_entry)
            session.commit()
            print(f"Weekly average saved: {weekly_avg}W (Week: {week_start}->{current_date})")

            session.query(DeviceDailyConsumption).filter(DeviceDailyConsumption.device_id == device_id,DeviceDailyConsumption.date >= week_start,DeviceDailyConsumption.date <= current_date).delete()
            session.commit()
            print("Daily data cleared after weekly aggregation.")
            return weekly_avg
        else:
            print("No daily data for weekly consumption.")
            return None
    except Exception as e:
        session.rollback()
        print(f"Error computing weekly consumption: {e}")
        sys.exit()