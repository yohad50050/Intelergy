from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    Float,
    func,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import ENUM
from datetime import datetime

from device_data_collector.db import Base, session


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())

    profiles = relationship(
        "Profile", back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="profiles")
    rooms = relationship("Room", back_populates="profile", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    profile_id = Column(
        Integer, ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False
    )

    profile = relationship("Profile", back_populates="rooms")
    devices = relationship(
        "Device", back_populates="room", cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    device_url = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(Enum("ON", "OFF"), default="OFF")
    room_id = Column(
        Integer, ForeignKey("rooms.room_id", ondelete="CASCADE"), nullable=False
    )

    room = relationship("Room", back_populates="devices")
    minutely_consumptions = relationship(
        "MinutelyConsumption", back_populates="device", cascade="all, delete-orphan"
    )
    hourly_consumptions = relationship(
        "HourlyConsumption", back_populates="device", cascade="all, delete-orphan"
    )
    weekly_consumptions = relationship(
        "DeviceWeeklyConsumption", back_populates="device", cascade="all, delete-orphan"
    )
    historical_hourly_consumptions = relationship(
        "HistoricalHourlyConsumption",
        back_populates="device",
        cascade="all, delete-orphan",
    )
    daily_consumptions = relationship(
        "DeviceDailyConsumption", back_populates="device", cascade="all, delete-orphan"
    )


class MinutelyConsumption(Base):
    __tablename__ = "minutely_consumptions"

    consumption_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    power_consumption = Column(Float, nullable=False)
    time = Column(DateTime, nullable=False)

    device = relationship("Device", back_populates="minutely_consumptions")


class HourlyConsumption(Base):
    __tablename__ = "hourly_consumptions"

    consumption_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    power_consumption = Column(Float, nullable=False)
    time = Column(DateTime, nullable=False)

    device = relationship("Device", back_populates="hourly_consumptions")


class HistoricalHourlyConsumption(Base):
    __tablename__ = "historical_hourly_consumptions"

    consumption_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    start_time = Column(DateTime, nullable=False)
    average_historical_power = Column(Float, nullable=False)

    device = relationship("Device", back_populates="historical_hourly_consumptions")


class DeviceDailyConsumption(Base):
    __tablename__ = "device_daily_consumptions"

    consumption_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    daily_average = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="regular")

    device = relationship("Device", back_populates="daily_consumptions")


class DeviceWeeklyConsumption(Base):
    __tablename__ = "weekly_consumptions"

    consumption_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    weekly_average = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

    device = relationship("Device", back_populates="weekly_consumptions")


# Base.metadata.drop_all(bind=session.get_bind())
