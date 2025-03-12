# data_processor.py

import time
from datetime import datetime, timezone
from db_manager import save_minutely_consumption,compute_and_save_hourly_consumption,compute_and_save_daily_consumption,compute_and_save_weekly_consumption
from mqtt_client import get_latest_power, get_device_id

def process_data():
    
    #Periodically reads 'latest_power' and 'device_id' from mqtt_client,
    #saves minutely data, and does aggregator logic.
    
    minutecounter = 0
    hourly_counter = 0
    daily_counter = 0

    
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24
    DAYS_PER_WEEK = 7

    while True:
        latest_p = get_latest_power()
        dev_id = get_device_id()

        if latest_p is not None and dev_id is not None:
            current_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            current_date = current_time.date()

            # Save minutely
            save_minutely_consumption(current_time, latest_p, dev_id)
            minutecounter += 1
            print(f"Minute-Counter: {minutecounter}")

            # Hourly
            if minutecounter >= MINUTES_PER_HOUR:
                hourly_avg = compute_and_save_hourly_consumption(current_time, dev_id)
                if hourly_avg is not None:
                    hourly_counter += 1
                    print(f"Hourly-Counter: {hourly_counter}")
                minutecounter = 0

                # Daily
                if hourly_counter >= HOURS_PER_DAY:
                    daily_avg = compute_and_save_daily_consumption(current_date, dev_id)
                    if daily_avg is not None:
                        daily_counter += 1
                        print(f"Daily-Counter: {daily_counter}")
                    hourly_counter = 0

                    # Weekly
                    if daily_counter >= DAYS_PER_WEEK:
                        compute_and_save_weekly_consumption(current_date, dev_id)
                        daily_counter = 0
        else:
            print("Waiting for power data...")

        time.sleep(60)