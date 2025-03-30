import time
import requests
from datetime import datetime, timezone

# Use package imports:
from device_data_collector.models import (
    Profile,
    User,
    Room,
    Device,
    MinutelyConsumption,
)
from device_data_collector.db import db
from device_data_collector.data_proccessor import data_processor


def fetch_shelly_power(url):
    try:
        r = requests.get(f"{url}/rpc/Shelly.GetStatus", timeout=5)
        if r.status_code == 200:
            return r.json().get("switch:0", {}).get("apower", 0.0)
        if r.status_code == 404:
            r = requests.get(f"{url}/status", timeout=5)
            if r.status_code == 200:
                return r.json().get("meters", [{}])[0].get("power", 0.0)
        return None
    except:
        return None


def create_new_profile():
    users = db.Session.query(User).all()
    if not users:
        print("No users found. Let's create one first.")
        uname = input("Enter user name: ")
        uemail = input("Enter user email: ")
        upass = input("Enter user password: ")
        new_u = User(user_name=uname, email=uemail, password=upass)
        db.Session.add(new_u)
        db.Session.commit()
        users = [new_u]

    print("Pick a user:")
    for u in users:
        print(u.user_id, u.user_name)
    choice = input("Enter user ID: ").strip() or str(users[0].user_id)
    user = db.session.query(User).filter_by(user_id=choice).first()
    pname = input("Enter profile name: ")
    new_p = Profile(name=pname, user_id=user.user_id)
    db.Session.add(new_p)
    db.Session.commit()


def create_new_room():
    profs = db.Session.query(Profile).all()
    if not profs:
        return
    print("Pick a profile:")
    for p in profs:
        print(p.profile_id, p.name)
    choice = input("Enter profile ID: ").strip() or str(profs[0].profile_id)
    prof = db.Session.query(Profile).filter_by(profile_id=choice).first()
    rname = input("Enter room name: ")
    new_r = Room(name=rname, profile_id=prof.profile_id)
    db.Session.add(new_r)
    db.Session.commit()


def create_new_device():
    url = input("Device URL (e.g. http://192.168.1.10): ").strip()
    existing = db.Session.query(Device).filter_by(device_url=url).first()
    if existing:
        print("Device with that URL already exists.")
        return
    if fetch_shelly_power(url) is None:
        print("Device unreachable.")
        return

    name = input("Device name: ").strip()
    dtype = input("Device type (TV/AC/etc.): ").strip()

    profs = db.Session.query(Profile).all()
    if not profs:
        create_new_profile()
        profs = db.Session.query(Profile).all()
        if not profs:
            return
    print("Pick a profile:")
    for p in profs:
        print(p.profile_id, p.name)
    pchoice = input("Profile ID: ").strip() or str(profs[0].profile_id)
    prof = db.Session.query(Profile).filter_by(profile_id=pchoice).first()

    if not prof.rooms:
        rname = input("Enter room name: ")
        new_r = Room(name=rname, profile_id=prof.profile_id)
        db.Session.add(new_r)
        db.Session.commit()
        chosen_room = new_r
    else:
        print("Pick a room:")
        for r in prof.rooms:
            print(r.room_id, r.name)
        rchoice = input("Room ID: ").strip() or str(prof.rooms[0].room_id)
        chosen_room = db.Session.query(Room).filter_by(room_id=rchoice).first()
        if not chosen_room:
            chosen_room = prof.rooms[0]

    new_d = Device(
        device_url=url, name=name, status="ON", type=dtype, room_id=chosen_room.room_id
    )
    db.Session.add(new_d)
    db.Session.commit()


def show_menu():
    while True:
        print("\n--- Menu ---")
        print("1) Add new profile")
        print("2) Add new room")
        print("3) Add new device")
        print("4) Continue to data collection")
        c = input("> ").strip()
        if c == "1":
            create_new_profile()
        elif c == "2":
            create_new_room()
        elif c == "3":
            create_new_device()
        elif c == "4":
            break


def run_data_collector():
    show_menu()
    print("Starting collector. Ctrl+C to stop.")
    last_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    while True:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if now > last_minute:
            devs = db.Session.query(Device).all()
            for d in devs:
                if d.status == "ON":
                    pw = fetch_shelly_power(d.device_url)
                    if pw is not None:
                        rec = MinutelyConsumption(
                            device_id=d.device_id, power_consumption=pw, time=now
                        )
                        db.Session.add(rec)
                        print(f"Logged {pw}W for {d.name}")
            db.Session.commit()
            data_processor()
            last_minute = now
        else:
            time.sleep(1)


if __name__ == "__main__":
    run_data_collector()
