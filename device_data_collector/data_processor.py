import logging
import time
from datetime import datetime
from sqlalchemy import desc
from device_data_collector.db import db
from device_data_collector.models import (
    Device,
    MinutelyConsumption,
    HourlyConsumption,
    DeviceDailyConsumption,
    DeviceWeeklyConsumption,
)

logger = logging.getLogger(__name__)


def aggregate_hourly():
    """
    Find the 60 newest minutely logs per device, if exactly 60 exist, create HourlyConsumption
    and delete them.
    """
    try:
        with db.get_session() as session:
            any_aggregated = False
            devices = session.query(Device).all()

            for device in devices:
                recent_minutely = (
                    session.query(MinutelyConsumption)
                    .filter(MinutelyConsumption.device_id == device.device_id)
                    .filter(MinutelyConsumption.power_consumption > 1)
                    .order_by(desc(MinutelyConsumption.time))
                    .limit(60)
                    .all()
                )

                if len(recent_minutely) == 60:
                    logs_sorted = sorted(recent_minutely, key=lambda x: x.time)
                    avg_power = sum(m.power_consumption for m in logs_sorted) / 60

                    hour_entry = HourlyConsumption(
                        device_id=device.device_id,
                        power_consumption=avg_power,
                        time=datetime.now(),
                    )
                    session.add(hour_entry)

                    for m in recent_minutely:
                        session.delete(m)

                    any_aggregated = True

            if any_aggregated:
                logger.info("Hourly aggregation done.")
    except Exception as e:
        logger.error(f"Error in hourly aggregation: {str(e)}")
        raise


def aggregate_daily():
    """
    Find the 24 newest hourly logs (aggregated=False) per device, if exactly 24 then
    create DeviceDailyConsumption and mark them aggregated.
    """
    try:
        with db.get_session() as session:
            any_aggregated = False
            devices = session.query(Device).all()

            for device in devices:
                recent_hourly = (
                    session.query(HourlyConsumption)
                    .filter(HourlyConsumption.device_id == device.device_id)
                    .filter(HourlyConsumption.aggregated == False)
                    .order_by(desc(HourlyConsumption.time))
                    .limit(24)
                    .all()
                )

                if len(recent_hourly) == 24:
                    logs_sorted = sorted(recent_hourly, key=lambda x: x.time)
                    avg_day = sum(h.power_consumption for h in logs_sorted) / 24

                    daily_entry = DeviceDailyConsumption(
                        device_id=device.device_id,
                        daily_average=avg_day,
                        date=datetime.now(),
                        status="regular",
                    )
                    session.add(daily_entry)

                    for h in recent_hourly:
                        h.aggregated = True

                    any_aggregated = True

            if any_aggregated:
                logger.info("Daily aggregation done.")
    except Exception as e:
        logger.error(f"Error in daily aggregation: {str(e)}")
        raise


def aggregate_weekly():
    """
    Find the 7 newest daily logs (aggregated=False) per device, if exactly 7 then
    create DeviceWeeklyConsumption and mark them aggregated.
    """
    try:
        with db.get_session() as session:
            any_aggregated = False
            devices = session.query(Device).all()

            for device in devices:
                recent_daily = (
                    session.query(DeviceDailyConsumption)
                    .filter(DeviceDailyConsumption.device_id == device.device_id)
                    .filter(DeviceDailyConsumption.aggregated == False)
                    .order_by(desc(DeviceDailyConsumption.date))
                    .limit(7)
                    .all()
                )

                if len(recent_daily) == 7:
                    logs_sorted = sorted(recent_daily, key=lambda x: x.date)
                    avg_week = sum(d.daily_average for d in logs_sorted) / 7

                    weekly_entry = DeviceWeeklyConsumption(
                        device_id=device.device_id,
                        weekly_average=avg_week,
                        date=datetime.now(),
                        status="regular",
                    )
                    session.add(weekly_entry)

                    for d in recent_daily:
                        d.aggregated = True

                    any_aggregated = True

            if any_aggregated:
                logger.info("Weekly aggregation done.")
    except Exception as e:
        logger.error(f"Error in weekly aggregation: {str(e)}")
        raise


def data_processor():
    current_minute = datetime.now().minute
    while True:
        now = datetime.now()
        if now.minute != current_minute:
            current_minute = now.minute
            try:
                aggregate_hourly()
                aggregate_daily()
                aggregate_weekly()
                logger.info("Data processing completed.")
            except Exception as e:
                logger.error(f"Error in data processing: {str(e)}")
                raise
        time.sleep(5)
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data_processor()