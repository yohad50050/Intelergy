from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    func,
    Table,
    Numeric,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.mysql import ENUM

# Database Setup
engine = create_engine(
    "mysql+mysqlconnector://root:MyNewPass@localhost/Intelergy", echo=True
)

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True


class User(BaseModel):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), unique=True, nullable=False)
    profiles = relationship("Profile", backref="user")


class Profile(BaseModel):
    __tablename__ = "profile"
    profile_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(ForeignKey("users.user_id"))
    rooms = relationship("Room", backref="profile")


class Room(BaseModel):
    __tablename__ = "rooms"
    room_id = Column(Integer, primary_key=True)
    profile_id = Column(ForeignKey("profile.profile_id"))
    name = Column(String(50), nullable=False)

    devices = relationship("Device", backref="room")


# Many-to-Many association for HistoricalHourlyConsumption with those Devices
historical_hourly_assoc = Table(
    "historical_hourly_assoc",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("hist_id", ForeignKey("historical_hourly_consumption.id")),
    Column("device_id", ForeignKey("devices.device_id")),
)


class Device(BaseModel):
    __tablename__ = "devices"
    device_id = Column(Integer, primary_key=True)
    room_id = Column(ForeignKey("rooms.room_id"))
    device_url = Column(String(100), nullable=False)
    name = Column(String(50), nullable=False)

    status = Column(
        ENUM("ON", "OFF", name="device_status"), nullable=False, default="OFF"
    )
    type = Column(
        ENUM("TV", "AC", "PC", "Fridge", name="type_of_device"), nullable=True
    )

    minutely_consumptions = relationship(
        "MinutelyConsumption", backref="device", cascade="all, delete"
    )
    device_daily_consumptions = relationship(
        "DeviceDailyConsumption", backref="device", cascade="all, delete"
    )
    device_weekly_consumptions = relationship(
        "DeviceWeeklyConsumption", backref="device", cascade="all, delete"
    )

    # Many-to-many with HistoricalHourlyConsumption
    historical_hourly_entries = relationship(
        "HistoricalHourlyConsumption",
        secondary=historical_hourly_assoc,
        back_populates="devices",
    )


class MinutelyConsumption(BaseModel):
    __tablename__ = "minutely_consumption"
    id = Column(Integer, primary_key=True)
    power_consumption = Column(Numeric(10, 2), default=0.00)
    time = Column(DateTime, default=func.now())
    device_id = Column(ForeignKey("devices.device_id"))


class DeviceDailyConsumption(BaseModel):
    __tablename__ = "daily_consumption"
    usage_log_id = Column(Integer, primary_key=True)
    daily_average = Column(Numeric(10, 2), default=0.00)
    status = Column(
        ENUM("irregular", "regular", name="regularity"),
        nullable=False,
        default="regular",
    )
    date = Column(Date, default=func.current_date())
    device_id = Column(Integer, ForeignKey("devices.device_id"))


class DeviceWeeklyConsumption(BaseModel):
    __tablename__ = "weekly_consumption"
    usage_log_id = Column(Integer, primary_key=True)
    weekly_average = Column(Numeric(10, 2), default=0.00)
    status = Column(
        ENUM("irregular", "regular", name="regularity"),
        nullable=False,
        default="regular",
    )
    date = Column(Date, default=func.current_date())
    device_id = Column(Integer, ForeignKey("devices.device_id"))


class HistoricalHourlyConsumption(BaseModel):
    __tablename__ = "historical_hourly_consumption"

    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=func.now())
    average_historical_power = Column(Numeric(10, 2), default=0.00)

    devices = relationship(
        "Device",
        secondary=historical_hourly_assoc,
        back_populates="historical_hourly_entries",
    )


# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
