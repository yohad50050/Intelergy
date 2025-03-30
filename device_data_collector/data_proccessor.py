from datetime import datetime
from collections import deque

# CHANGED THESE IMPORTS:
from device_data_collector.models import (
    Device,
    MinutelyConsumption,
    HistoricalHourlyConsumption,
    DeviceDailyConsumption,
    DeviceWeeklyConsumption,
)
from device_data_collector.db import db


def aggregate_hourly():
    db.session.expire_all()
    devices = db.session.query(Device).all()
    for d in devices:
        logs = (
            db.session.query(MinutelyConsumption)
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
                device_id=d.device_id, start_time=start, average_historical_power=avg
            )
            db.session.add(h)
            for used in block:
                db.session.delete(used)
            zeros = (
                db.session.query(MinutelyConsumption)
                .filter_by(power_consumption=0)
                .all()
            )
            for z in zeros:
                db.session.delete(z)
            db.session.commit()


def aggregate_daily():
    db.session.expire_all()
    devices = db.session.query(Device).all()
    for d in devices:
        rows = (
            db.session.query(HistoricalHourlyConsumption)
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
            db.session.add(daily)
            for used in block:
                db.session.delete(used)
            db.session.commit()


def aggregate_weekly():
    db.session.expire_all()
    devices = db.session.query(Device).all()
    for d in devices:
        rows = (
            db.session.query(DeviceDailyConsumption)
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
                device_id=d.device_id, weekly_average=avg, date=wstart, status="regular"
            )
            db.session.add(weekly)
            for used in block:
                db.session.delete(used)
            db.session.commit()


def data_processor():
    aggregate_hourly()
    aggregate_daily()
    aggregate_weekly()


if __name__ == "__main__":
    data_processor()
