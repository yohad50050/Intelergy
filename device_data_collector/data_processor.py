from datetime import datetime, timedelta
from sqlalchemy import func
from device_data_collector.models import Device, MinutelyConsumption, HourlyConsumption
from device_data_collector.db import db
import logging
from collections import deque
from device_data_collector.models import (
    HistoricalHourlyConsumption,
    DeviceDailyConsumption,
    DeviceWeeklyConsumption,
)

logger = logging.getLogger(__name__)


def aggregate_hourly():
    """Aggregate minutely data into hourly averages"""
    try:
        with db.get_session() as session:
            devs = session.query(Device).all()
            for d in devs:
                logs = (
                    session.query(MinutelyConsumption)
                    .filter_by(device_id=d.device_id)
                    .filter(MinutelyConsumption.power_consumption > 0)
                    .order_by(MinutelyConsumption.time.asc())
                    .all()
                )
                q = deque(logs)
                while len(q) >= 60:
                    block = [q.popleft() for _ in range(60)]
                    avg = sum(x.power_consumption for x in block) / 60
                    start = block[0].time.replace(second=0, microsecond=0)
                    h = HistoricalHourlyConsumption(
                        device_id=d.device_id,
                        start_time=start,
                        average_historical_power=avg,
                    )
                    session.add(h)
                    for used in block:
                        session.delete(used)

                    zeroes = (
                        session.query(MinutelyConsumption)
                        .filter_by(power_consumption=0)
                        .all()
                    )
                    for z in zeroes:
                        session.delete(z)

            logger.info("Hourly aggregation completed successfully")
    except Exception as e:
        logger.error(f"Error in hourly aggregation: {str(e)}")
        raise


def aggregate_daily():
    """Aggregate hourly data into daily averages"""
    try:
        with db.get_session() as session:
            devs = session.query(Device).all()
            for d in devs:
                rows = (
                    session.query(HistoricalHourlyConsumption)
                    .filter_by(device_id=d.device_id)
                    .order_by(HistoricalHourlyConsumption.start_time.asc())
                    .all()
                )
                q = deque(rows)
                while len(q) >= 24:
                    block = [q.popleft() for _ in range(24)]
                    avg = sum(x.average_historical_power for x in block) / 24
                    day_date = block[0].start_time.date()
                    daily = DeviceDailyConsumption(
                        device_id=d.device_id,
                        daily_average=avg,
                        date=day_date,
                        status="regular",
                    )
                    session.add(daily)
                    for used in block:
                        session.delete(used)

            logger.info("Daily aggregation completed successfully")
    except Exception as e:
        logger.error(f"Error in daily aggregation: {str(e)}")
        raise


def aggregate_weekly():
    """Aggregate daily data into weekly averages"""
    try:
        with db.get_session() as session:
            devs = session.query(Device).all()
            for d in devs:
                rows = (
                    session.query(DeviceDailyConsumption)
                    .filter_by(device_id=d.device_id)
                    .order_by(DeviceDailyConsumption.date.asc())
                    .all()
                )
                q = deque(rows)
                while len(q) >= 7:
                    block = [q.popleft() for _ in range(7)]
                    avg = sum(x.daily_average for x in block) / 7
                    wstart = block[0].date
                    weekly = DeviceWeeklyConsumption(
                        device_id=d.device_id,
                        weekly_average=avg,
                        date=wstart,
                        status="regular",
                    )
                    session.add(weekly)
                    for used in block:
                        session.delete(used)

            logger.info("Weekly aggregation completed successfully")
    except Exception as e:
        logger.error(f"Error in weekly aggregation: {str(e)}")
        raise


def data_processor():
    """Process data aggregation at all levels"""
    try:
        aggregate_hourly()
        aggregate_daily()
        aggregate_weekly()
        logger.info("Data processing completed successfully")
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        raise


if __name__ == "__main__":
    data_processor()
