from datetime import datetime, timedelta
from sqlalchemy import func
from device_data_collector.models import Device, MinutelyConsumption, HourlyConsumption
from device_data_collector.db import db
import logging

logger = logging.getLogger(__name__)


def aggregate_hourly():
    """Aggregate minutely data into hourly averages"""
    try:
        with db.get_session() as session:
            # Get all devices
            devices = session.query(Device).all()

            for device in devices:
                # Get the last hour's worth of minutely data
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)

                # Calculate hourly average
                hourly_avg = (
                    session.query(func.avg(MinutelyConsumption.power_consumption))
                    .filter(
                        MinutelyConsumption.device_id == device.device_id,
                        MinutelyConsumption.time >= one_hour_ago,
                    )
                    .scalar()
                )

                if hourly_avg is not None:
                    # Create new hourly consumption record
                    new_hourly = HourlyConsumption(
                        device_id=device.device_id,
                        power_consumption=hourly_avg,
                        time=datetime.utcnow(),
                    )
                    session.add(new_hourly)

                    # Delete minutely data older than 1 hour
                    session.query(MinutelyConsumption).filter(
                        MinutelyConsumption.device_id == device.device_id,
                        MinutelyConsumption.time < one_hour_ago,
                    ).delete()

            session.commit()
            logger.info("Hourly aggregation completed successfully")

    except Exception as e:
        logger.error(f"Error in hourly aggregation: {str(e)}")
        raise
