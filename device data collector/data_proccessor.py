from datetime import datetime, timedelta
from collections import deque
from models import (session,Device,MinutelyConsumption,HistoricalHourlyConsumption,DeviceDailyConsumption,DeviceWeeklyConsumption)

def aggregate_hourly():
    
    ## For each device:
    ##   1. Gather non-zero minutely logs in ascending time order.
    ##   2. Whenever we have 60 logs, create an hourly record.
    ##   3. Remove those 60 logs from the DB.
    ##   4. Also remove zero-power logs each time (so they don't pile up).
    
    print("[aggregate_hourly] Starting...")
    session.expire_all()

    all_devices = session.query(Device).all()
    for device in all_devices:
        print(f"  Checking device {device.device_id} ({device.name}) for hourly aggregation...")
        nonzero_logs = (session.query(MinutelyConsumption).filter(MinutelyConsumption.device_id == device.device_id).filter(MinutelyConsumption.power_consumption > 0).order_by(MinutelyConsumption.time.asc()).all())

        logs_queue = deque(nonzero_logs)
        while len(logs_queue) >= 60:

            sixty_logs = []
            for i in range(60):
                popped_log = logs_queue.popleft()
                sixty_logs.append(popped_log)

            total_power = 0
            for log in sixty_logs:
                total_power += log.power_consumption
            average_power = float(total_power) / 60.0
            start_time = sixty_logs[0].time.replace(second=0, microsecond=0)

            new_hourly_record = HistoricalHourlyConsumption(start_time=start_time,average_historical_power=average_power)
            new_hourly_record.devices.append(device)
            session.add(new_hourly_record)

            # Remove 60 non-zero from DB
            for used_log in sixty_logs:
                session.delete(used_log)

            # Remove zero from DB
            zero_logs = (session.query(MinutelyConsumption).filter(MinutelyConsumption.power_consumption == 0).all())
            for zero_log in zero_logs:
                session.delete(zero_log)

            session.commit()
            print(f"    + Hourly record created ({average_power:.2f} W), removed 60 logs plus zero logs if any.")

    print("[aggregate_hourly] Done.\n")

def aggregate_daily():
    
    ## For each device:
    ##   1. Gather hourly logs from DB in ascending order.
    ##   2. Whenever we have 24 logs, create a daily record and remove them.
    
    print("[aggregate_daily] Starting...")
    session.expire_all()

    all_devices = session.query(Device).all()
    for device in all_devices:
        print(f"  Checking device {device.device_id} ({device.name}) for daily aggregation...")
        hourly_rows = (session.query(HistoricalHourlyConsumption).join(HistoricalHourlyConsumption.devices).filter(Device.device_id == device.device_id).order_by(HistoricalHourlyConsumption.start_time.asc()).all())

        row_queue = deque(hourly_rows)
        while len(row_queue) >= 24:
            twenty_four_hours = []
            for i in range(24):
                popped_row = row_queue.popleft()
                twenty_four_hours.append(popped_row)

            total_power = 0
            for h in twenty_four_hours:
                total_power += h.average_historical_power
            daily_average = float(total_power) / 24.0
            day_date = twenty_four_hours[0].start_time.date()

            new_daily_record = DeviceDailyConsumption(daily_average=daily_average,date=day_date,device_id=device.device_id,status='regular')
            session.add(new_daily_record)

            for hourly_row in twenty_four_hours:
                session.delete(hourly_row)

            session.commit()
            print(f"    + Daily record created for {day_date}, avg={daily_average:.2f}, removed 24 hourly rows.")

    print("[aggregate_daily] Done.\n")

def aggregate_weekly():
    
    ## For each device:
    ##   1. Gather daily logs in ascending date order.
    ##   2. Whenever we have 7, create a weekly record and remove them.
    
    print("[aggregate_weekly] Starting...")
    session.expire_all()

    all_devices = session.query(Device).all()
    for device in all_devices:
        print(f"  Checking device {device.device_id} ({device.name}) for weekly aggregation...")
        daily_rows = (session.query(DeviceDailyConsumption).filter(DeviceDailyConsumption.device_id == device.device_id).order_by(DeviceDailyConsumption.date.asc()).all())

        row_queue = deque(daily_rows)
        while len(row_queue) >= 7:
            seven_days = []
            for i in range(7):
                popped_day = row_queue.popleft()
                seven_days.append(popped_day)

            total_daily = 0
            for day in seven_days:
                total_daily += day.daily_average
            weekly_average = total_daily / 7.0
            week_start = seven_days[0].date

            new_weekly_record = DeviceWeeklyConsumption(weekly_average=weekly_average,date=week_start,device_id=device.device_id,status='regular')
            session.add(new_weekly_record)

            for day_record in seven_days:
                session.delete(day_record)

            session.commit()
            print(f"    + Weekly record created starting {week_start}, avg={weekly_average:.2f}, removed 7 daily rows.")

    print("[aggregate_weekly] Done.\n")

def data_processor():
    
    ## Runs the entire pipeline:
    ##   1) Hourly aggregation (60 minutely => 1 hour)
    ##   2) Daily aggregation (24 hours => 1 day)
    ##   3) Weekly aggregation (7 days => 1 week)
    
    print("[data_processor] Starting aggregation pipeline.")
    aggregate_hourly()
    aggregate_daily()
    aggregate_weekly()
    print("[data_processor] Aggregation complete.\n")


if __name__ == "__main__":
    data_processor()
