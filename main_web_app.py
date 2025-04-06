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
    HourlyConsumption,
    DeviceDailyConsumption,
)
from datetime import datetime, timezone
import requests
from device_data_collector.db import db
import re
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")

# Initialize database tables only if they don't exist
try:
    # Check if tables exist by trying to query the users table
    with db.get_session() as session:
        session.query(User).first()
except Exception as e:
    app.logger.info("Tables don't exist, creating them...")
    try:
        db.create_tables()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")

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


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Basic validation
        if not all([username, email, password, confirm_password]):
            return render_template("signup.html", error="All fields are required")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match")

        # Email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return render_template("signup.html", error="Invalid email format")

        # Check if user already exists
        with db.get_session() as session:
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                return render_template("signup.html", error="Email already registered")

            # Create new user
            try:
                new_user = User(
                    user_name=username,
                    email=email,
                    password=password,  # In a real app, hash the password!
                )
                session.add(new_user)
                session.commit()

                # Log the user in
                login_user(UserWrapper(new_user))
                flash("Account created successfully!")
                return redirect(url_for("index"))
            except Exception as e:
                app.logger.error(f"Error creating user: {str(e)}")
                return render_template(
                    "signup.html", error="Error creating account. Please try again."
                )

    return render_template("signup.html")


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
    time_range = request.args.get("time_range", "minutely")

    with db.get_session() as session:
        device = session.query(Device).filter_by(device_id=device_id).first()
        if not device:
            app.logger.error(f"Device {device_id} not found")  # Debug log
            return jsonify({"error": "Device not found"}), 404

        # Verify the device belongs to the current user
        room = session.query(Room).filter_by(room_id=device.room_id).first()
        profile = session.query(Profile).filter_by(profile_id=room.profile_id).first()
        if profile.user_id != current_user.id:
            return jsonify({"error": "Access denied"}), 403

        response = {}

        if time_range == "minutely":
            # Get the latest minutely consumption
            latest_consumption = (
                session.query(MinutelyConsumption)
                .filter_by(device_id=device_id)
                .order_by(MinutelyConsumption.time.desc())
                .first()
            )
            response = {
                "power": (
                    float(latest_consumption.power_consumption)
                    if latest_consumption
                    else None
                ),
                "last_updated": (
                    latest_consumption.time.isoformat() if latest_consumption else None
                ),
            }
        elif time_range == "hourly":
            # Get the latest hourly consumption
            hourly_consumption = (
                session.query(HourlyConsumption)
                .filter_by(device_id=device_id)
                .order_by(HourlyConsumption.time.desc())
                .first()
            )
            response = {
                "hourly_average": (
                    float(hourly_consumption.power_consumption)
                    if hourly_consumption
                    else None
                ),
                "last_updated": (
                    hourly_consumption.time.isoformat() if hourly_consumption else None
                ),
            }
        elif time_range == "daily":
            # Get the latest daily consumption
            daily_consumption = (
                session.query(DeviceDailyConsumption)
                .filter_by(device_id=device_id)
                .order_by(DeviceDailyConsumption.date.desc())
                .first()
            )
            response = {
                "daily_average": (
                    float(daily_consumption.daily_average)
                    if daily_consumption
                    else None
                ),
                "last_updated": (
                    daily_consumption.date.isoformat() if daily_consumption else None
                ),
            }
        elif time_range == "weekly":
            # Get the latest weekly consumption
            weekly_consumption = (
                session.query(DeviceWeeklyConsumption)
                .filter_by(device_id=device_id)
                .order_by(DeviceWeeklyConsumption.date.desc())
                .first()
            )
            response = {
                "weekly_average": (
                    float(weekly_consumption.weekly_average)
                    if weekly_consumption
                    else None
                ),
                "last_updated": (
                    weekly_consumption.date.isoformat() if weekly_consumption else None
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
    try:
        name = request.form.get("name")
        profile_id = request.form.get("profile_id")

        if not name or not profile_id:
            return jsonify({"error": "Missing room name or profile ID"}), 400

        # Verify the profile belongs to the current user
        with db.get_session() as session:
            profile = (
                session.query(Profile)
                .filter_by(profile_id=profile_id, user_id=current_user.id)
                .first()
            )

            if not profile:
                return jsonify({"error": "Profile not found"}), 404

            # Create new room
            new_room = Room(name=name, profile_id=profile_id)
            session.add(new_room)
            session.commit()

            # Check if request wants JSON response
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "room_id": new_room.room_id})
            else:
                # Regular form submission - redirect back to profile page
                return redirect(url_for("profile_view", profile_id=profile_id))

    except Exception as e:
        app.logger.error(f"Error creating room: {str(e)}")
        return jsonify({"error": "Failed to create room"}), 500


@app.route("/api/device/add", methods=["POST"])
@login_required
def add_device():
    try:
        room_id = request.form.get("room_id")
        name = request.form.get("name")
        device_url = request.form.get("device_url")
        device_type = request.form.get("type")

        if not all([room_id, name, device_url, device_type]):
            return jsonify({"error": "All fields are required"}), 400

        with db.get_session() as session:
            # First get the room to verify it exists and get its profile_id
            room = session.query(Room).filter_by(room_id=room_id).first()
            if not room:
                return jsonify({"error": "Room not found"}), 404

            # Verify the room belongs to the current user through the profile
            profile = (
                session.query(Profile)
                .filter_by(profile_id=room.profile_id, user_id=current_user.id)
                .first()
            )

            if not profile:
                return jsonify({"error": "Access denied"}), 403

            # Create new device
            new_device = Device(
                room_id=room_id,
                name=name,
                device_url=device_url,
                type=device_type,
                status="ON",
            )
            session.add(new_device)
            session.commit()

            # Check if request wants JSON response
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "device_id": new_device.device_id})
            else:
                # Regular form submission - redirect back to profile page
                return redirect(url_for("profile_view", profile_id=room.profile_id))

    except Exception as e:
        app.logger.error(f"Error adding device: {str(e)}")
        return jsonify({"error": "Failed to add device"}), 500


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


def toggle_shelly_device(device_url, turn_on):
    try:
        # Attempt Gen 2 (RPC)
        response = requests.post(
            f"{device_url}/rpc/Switch.Set", json={"id": 0, "on": turn_on}, timeout=5
        )
        if response.status_code == 200:
            return True

        # If 404, attempt Gen 1
        if response.status_code == 404:
            response = requests.get(
                f"{device_url}/relay/0?turn={'on' if turn_on else 'off'}", timeout=5
            )
            if response.status_code == 200:
                return True

        return False
    except requests.exceptions.RequestException:
        return False


@app.route("/api/device/<int:device_id>/toggle", methods=["POST"])
@login_required
def toggle_device(device_id):
    action = request.form.get("action")
    if action not in ["on", "off"]:
        return jsonify({"success": False, "error": "Invalid action"}), 400

    with db.get_session() as session:
        device = session.query(Device).filter_by(device_id=device_id).first()
        if not device:
            return jsonify({"success": False, "error": "Device not found"}), 404

        # Verify the device belongs to the current user
        room = session.query(Room).filter_by(room_id=device.room_id).first()
        profile = session.query(Profile).filter_by(profile_id=room.profile_id).first()
        if profile.user_id != current_user.id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Try to toggle the device
        success = toggle_shelly_device(device.device_url, action == "on")
        if success:
            device.status = "ON" if action == "on" else "OFF"
            session.commit()
            return jsonify({"success": True, "status": device.status})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to toggle device. Please check the device connection.",
                    }
                ),
                500,
            )


if __name__ == "__main__":
    app.run(debug=True)
