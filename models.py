from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, DateTime, func, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.mysql import ENUM

# Database connection
engine = create_engine(
    'mysql+mysqlconnector://Yohad:159357@localhost/testdatabase',
    echo=True
)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define BaseModel class
class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

# 1) Users Table
class User(BaseModel):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), unique=True, nullable=False)
    profiles = relationship("Profile", backref="user")

# 2) Profiles Table
class Profile(BaseModel):
    __tablename__ = 'profile'
    profile_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(ForeignKey("users.user_id"))
    rooms = relationship("Room", backref="profile")

    def change_name(self, new_name, session):
        self.name = new_name
        session.commit()

    def delete_profile(self, session):
        session.delete(self)
        session.commit()

# 3) Rooms Table
class Room(BaseModel):
    __tablename__ = 'rooms'
    room_id = Column(Integer, primary_key=True)
    profile_id = Column(ForeignKey("profile.profile_id"))
    name = Column(String(50), nullable=False)
    devices = relationship("Device", backref="room")

    def changename(self, new_name, session):
        self.name = new_name
        session.commit()

# 4) Devices Table
class Device(BaseModel):
    __tablename__ = 'devices'
    device_id = Column(Integer, primary_key=True)
    room_id = Column(ForeignKey("rooms.room_id"))
    device_url = Column(String(100), nullable=False)
    name = Column(String(50), nullable=False)
    status = Column(ENUM('ON', 'OFF', name="device_status"), nullable=False, default='OFF')
    type = Column(ENUM('TV', 'AC', 'PC', 'Fridge', name="type_of_device"), nullable=True)

    # One-to-Many: Device -> MinutelyConsumption
    minutely_consumptions = relationship(
        "MinutelyConsumption",
        backref="device",
        cascade="all, delete"
    )

    # One-to-Many: Device -> HistoricalHourlyConsumption
    historical_hourly_consumptions = relationship(
        "HistoricalHourlyConsumption",
        backref="device",
        cascade="all, delete"
    )

# 5) Minutely Consumption Table
class MinutelyConsumption(BaseModel):
    __tablename__ = 'minutely_consumption'
    id = Column(Integer, primary_key=True)
    power_consumption = Column(Integer, default=0)
    time = Column(DateTime, default=func.now())
    device_id = Column(ForeignKey("devices.device_id"))

# 6) Historical Hourly Consumption Table
class HistoricalHourlyConsumption(BaseModel):
    __tablename__ = 'historical_hourly_consumption'
    id = Column(Integer, primary_key=True)
    status = Column(
        ENUM('irregular', 'regular', name="regularity"),
        nullable=False,
        default='regular'
    )
    time = Column(DateTime, default=func.now())
    device_id = Column(ForeignKey("devices.device_id"))

class DeviceHourlyConsumption(BaseModel):
    __tablename__ = 'hourly_consumption'
    usage_log_id = Column(Integer, primary_key=True)
    hour_average_power = Column(Integer, default=0)
    status = Column(
        ENUM('irregular', 'regular', name="regularity"),
        nullable=False,
        default='regular'
    )
    # Change to DateTime if you want a full timestamp
    time = Column(DateTime, default=func.now())

    # Many-to-Many with Device
    devices = relationship(
        "Device",
        secondary="device_hourly_association",
        backref="hourly_consumption_devices"
    )

# 8) Device Daily Consumption Table (via Many-to-Many)
class DeviceDailyConsumption(BaseModel):
    __tablename__ = 'daily_consumption'
    usage_log_id = Column(Integer, primary_key=True)
    daily_average = Column(Integer, default=0)
    status = Column(
        ENUM('irregular', 'regular', name="regularity"),
        nullable=False,
        default='regular'
    )
    date = Column(Date, default=func.current_date())

    # Many-to-Many with Device
    devices = relationship(
        "Device",
        secondary="device_daily_association",
        backref="daily_consumption_devices"
    )

# 9) Device Weekly Consumption Table (via Many-to-Many)
class DeviceWeeklyConsumption(BaseModel):
    __tablename__ = 'weekly_consumption'
    usage_log_id = Column(Integer, primary_key=True)
    weekly_average = Column(Integer, default=0)
    status = Column(
        ENUM('irregular', 'regular', name="regularity"),
        nullable=False,
        default='regular'
    )
    date = Column(Date, default=func.current_date())

    # Many-to-Many with Device
    devices = relationship(
        "Device",
        secondary="device_weekly_association",
        backref="weekly_consumption_devices"
    )

# 10) Association Tables for Many-to-Many
class DeviceHourlyAssociation(BaseModel):
    __tablename__ = 'device_hourly_association'
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    hourly_consumption_id = Column(Integer, ForeignKey("hourly_consumption.usage_log_id"))

class DeviceDailyAssociation(BaseModel):
    __tablename__ = 'device_daily_association'
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    daily_consumption_id = Column(Integer, ForeignKey("daily_consumption.usage_log_id"))

class DeviceWeeklyAssociation(BaseModel):
    __tablename__ = 'device_weekly_association'
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    weekly_consumption_id = Column(Integer, ForeignKey("weekly_consumption.usage_log_id"))


from sqlalchemy import inspect, text

# Inspect the current table columns
inspector = inspect(engine)
columns = inspector.get_columns('hourly_consumption')
existing_col_names = [col['name'] for col in columns]

from sqlalchemy import text

# Connect to the database and drop columns
with engine.connect() as connection:
    # Only run these if the columns exist
    try:
        connection.execute(text("ALTER TABLE hourly_consumption DROP COLUMN date;"))
        print("✅ Dropped 'date' column from hourly_consumption.")
    except Exception as e:
        print(f"⚠️ Could not drop 'date': {e}")

    try:
        connection.execute(text("ALTER TABLE hourly_consumption DROP COLUMN hourly_average;"))
        print("✅ Dropped 'hourly_average' column from hourly_consumption.")
    except Exception as e:
        print(f"⚠️ Could not drop 'hourly_average': {e}")