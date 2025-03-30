import time
import logging
from datetime import datetime
import requests
from device_data_collector.models import Device, MinutelyConsumption
from device_data_collector.db import db
from device_data_collector.data_processor import aggregate_hourly

logger = logging.getLogger(__name__)


def fetch_device_power(device_url):
    ## Fetch power consumption from a Shelly device
    try:
        # Try Gen 2 API first
        response = requests.get(f"{device_url}/rpc/Shelly.GetStatus", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("switch:0", {}).get("apower", 0.0)

        # If that fails, try Gen 1 API
        if response.status_code == 404:
            response = requests.get(f"{device_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("meters", [{}])[0].get("power", 0.0)

        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching power data: {str(e)}")
        return None


def collect_data():
    ## Collect power consumption data from all devices
    try:
        with db.get_session() as session:
            # Get all devices
            devices = session.query(Device).all()

            if not devices:
                logger.info(
                    "No devices found in database. Waiting for devices to be added..."
                )
                return

            for device in devices:
                power = fetch_device_power(device.device_url)

                if power is not None:
                    # Create new consumption record
                    new_consumption = MinutelyConsumption(
                        device_id=device.device_id,
                        power_consumption=power,
                        time=datetime.utcnow(),
                    )
                    session.add(new_consumption)
                    logger.info(
                        f"Collected power data for device {device.device_id}: {power}W"
                    )
                else:
                    logger.warning(
                        f"Failed to collect power data for device {device.device_id}"
                    )

            session.commit()

    except Exception as e:
        logger.error(f"Error collecting data: {str(e)}")
        raise


def run_data_collector():
    """Main function to run the data collection process"""
    logger.info("Starting data collector...")

    hourly_counter = 0

    while True:
        try:
            # Collect data every minute
            collect_data()

            # Increment counter and check if an hour has passed
            hourly_counter += 1
            if hourly_counter >= 60:
                aggregate_hourly()
                hourly_counter = 0

            # Wait for next minute
            time.sleep(60)

        except Exception as e:
            logger.error(f"Error in data collector: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_data_collector()
