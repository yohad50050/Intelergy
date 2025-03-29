from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from device_data_collector.models import (
    User,
    Profile,
    Room,
    Device,
    MinutelyConsumption,
    DeviceWeeklyConsumption,
)
from datetime import datetime, timezone
import requests
from device_data_collector.db import db

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # Change this to a secure secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class UserWrapper(UserMixin):
    def __init__(self, user):
        self.id = user.user_id
        self.username = user.user_name
        self.email = user.email


@login_manager.user_loader
def load_user(user_id):
    app.logger.debug(f"Loading user with ID: {user_id}")
    with db.get_session() as session:
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            return UserWrapper(user) if user else None
        except Exception as e:
            app.logger.error(f"Error loading user: {str(e)}")
            return None


def get_device_icon(device_type):
    icons = {"TV": "tv", "AC": "snowflake", "PC": "laptop", "Fridge": "refrigerator"}
    return icons.get(device_type, "plug")


# Register the template filter
app.jinja_env.filters["get_device_icon"] = get_device_icon


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        with db.get_session() as session:
            user = session.query(User).filter_by(email=email, password=password).first()
            if user:
                login_user(UserWrapper(user))
                return redirect(url_for("index"))
            else:
                return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    with db.get_session() as session:
        profiles = session.query(Profile).filter_by(user_id=current_user.id).all()
        return render_template("index.html", profiles=profiles)


@app.route("/profile/<int:profile_id>")
@login_required
def profile_view(profile_id):
    with db.get_session() as session:
        profile = (
            session.query(Profile)
            .filter_by(profile_id=profile_id, user_id=current_user.id)
            .first()
        )
        if not profile:
            return render_template("404.html"), 404
        rooms = session.query(Room).filter_by(profile_id=profile_id).all()
        return render_template("profile.html", profile=profile, rooms=rooms)


@app.route("/api/device/<int:device_id>/power")
@login_required
def get_device_power(device_id):
    app.logger.debug(f"Power request for device {device_id}")  # Debug log
    with db.get_session() as session:
        device = session.query(Device).filter_by(device_id=device_id).first()
        if not device:
            app.logger.error(f"Device {device_id} not found")  # Debug log
            return jsonify({"error": "Device not found"}), 404

        # Get the latest minutely consumption
        latest_consumption = (
            session.query(MinutelyConsumption)
            .filter_by(device_id=device_id)
            .order_by(MinutelyConsumption.time.desc())
            .first()
        )
        app.logger.debug(f"Latest consumption: {latest_consumption}")  # Debug log

        # Get the weekly average if it exists
        weekly_consumption = (
            session.query(DeviceWeeklyConsumption)
            .filter_by(device_id=device_id)
            .order_by(DeviceWeeklyConsumption.date.desc())
            .first()
        )
        app.logger.debug(f"Weekly consumption: {weekly_consumption}")  # Debug log

        response = {
            "power": (
                float(latest_consumption.power_consumption) if latest_consumption else 0
            ),
            "weekly_average": (
                float(weekly_consumption.weekly_average) if weekly_consumption else None
            ),
            "last_updated": (
                latest_consumption.time.isoformat() if latest_consumption else None
            ),
        }
        app.logger.debug(f"Sending response: {response}")  # Debug log
        return jsonify(response)


@app.route("/api/profile/add", methods=["POST"])
@login_required
def add_profile():
    name = request.form.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400

    with db.get_session() as session:
        new_profile = Profile(name=name, user_id=current_user.id)
        session.add(new_profile)
        session.commit()  # Explicit commit for write operations
        return jsonify({"success": True, "profile_id": new_profile.profile_id})


@app.route("/api/room/add", methods=["POST"])
@login_required
def add_room():
    profile_id = request.form.get("profile_id")
    name = request.form.get("name")

    if not name or not profile_id:
        return jsonify({"error": "Name and profile_id are required"}), 400

    with db.get_session() as session:
        profile = (
            session.query(Profile)
            .filter_by(profile_id=profile_id, user_id=current_user.id)
            .first()
        )
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        new_room = Room(name=name, profile_id=profile_id)
        session.add(new_room)
        session.commit()
        return jsonify({"success": True, "room_id": new_room.room_id})


@app.route("/api/device/add", methods=["POST"])
@login_required
def add_device():
    room_id = request.form.get("room_id")
    name = request.form.get("name")
    device_url = request.form.get("device_url")
    device_type = request.form.get("type")

    if not all([room_id, name, device_url, device_type]):
        return jsonify({"error": "All fields are required"}), 400

    with db.get_session() as session:
        room = session.query(Room).filter_by(room_id=room_id).first()
        if not room:
            return jsonify({"error": "Room not found"}), 404
        new_device = Device(
            room_id=room_id,
            name=name,
            device_url=device_url,
            type=device_type,
            status="ON",
        )
        session.add(new_device)
        session.commit()
        return jsonify({"success": True, "device_id": new_device.device_id})


def fetch_shelly_power(device_url):
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

        return None
    except requests.exceptions.RequestException:
        return None


if __name__ == "__main__":
    app.run(debug=True)
