import time
import logging
import requests
from datetime import datetime

from device_data_collector.db import db
from device_data_collector.models import Device, MinutelyConsumption
from device_data_collector.data_processor import data_processor

logger = logging.getLogger(__name__)


def fetch_device_power(device_url):
    """Fetch Shelly device power; None if unreachable."""
    try:
        resp = requests.get(f"{device_url}/rpc/Shelly.GetStatus", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("switch:0", {}).get("apower", 0.0)
        if resp.status_code == 404:
            resp = requests.get(f"{device_url}/status", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("meters", [{}])[0].get("power", 0.0)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error(f"Error fetching power data: {str(exc)}")
        return None


def collect_data():
    """Collect power data if >1W, otherwise mark device as OFF."""
    try:
        with db.get_session() as session:
            devices = session.query(Device).all()
            if not devices:
                logger.info("No devices found, waiting...")
                return

            for device in devices:
                power = fetch_device_power(device.device_url)
                if power and power > 1:
                    usage = MinutelyConsumption(
                        device_id=device.device_id,
                        power_consumption=power,
                        time=datetime.now(),
                    )
                    device.status = "ON"
                    session.add(usage)
                    session.commit()
                    logger.info(f"Device {device.device_id}: {power}W")
                else:
                    device.status = "OFF"
                    logger.info(
                        f"Device {device.device_id} is OFF (power={power or 0.0})"
                    )
    except Exception as err:
        logger.error(f"Error collecting data: {str(err)}")
        raise


def run_data_collector():
    """
    Check clock each second.
    If minute changes, collect & process.
    """
    logger.info("Starting data collector...")
    current_minute = datetime.now().minute

    while True:
        try:
            now = datetime.now()
            if now.minute != current_minute:
                current_minute = now.minute
                collect_data()
                data_processor()
            time.sleep(1)
        except Exception as err:
            logger.error(f"Error in collector loop: {str(err)}")
            time.sleep(5)


if __name__ == "__main__":
    # db.create_tables()  # Run once if needed
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_data_collector()
