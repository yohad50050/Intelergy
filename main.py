# main.py

from mqtt_client import start_mqtt
from data_processor import process_data

if __name__ == "__main__":
    print("Starting Smart Home Energy Monitoring System...")

    start_mqtt()   # Start MQTT in the background
    process_data() # Main aggregator loop