# mqtt_client.py

import json
import paho.mqtt.client as mqtt
import threading
from models import session, Device
from db_manager import prompt_and_add_new_device, update_device_status

BROKER = "192.168.1.150"
TOPIC = "shellyplugsg3-8cbfea974904/events/rpc"

latest_power = 0.0
device_id = None

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to topic: {TOPIC}")

def on_message(client, userdata, msg):
    global latest_power, device_id
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        switch_data = payload.get("params", {}).get("switch:0", {})
        amps = switch_data.get("current", 0.0)

        voltage = 230.0
        calc_power = round(voltage * amps, 2)  # watts

        print(f"MQTT → Device ID: {payload.get('src')}, Current={amps}A, ~{calc_power}W")

        shelly_device_id = payload.get("src")
        found_device = session.query(Device).filter_by(device_url=shelly_device_id).first()

        if found_device:
            device_id = found_device.device_id
            update_device_status(found_device, amps)
            latest_power = calc_power
        else:
            prompt_and_add_new_device(shelly_device_id)
            found_device = session.query(Device).filter_by(device_url=shelly_device_id).first()
            if found_device:
                device_id = found_device.device_id
                update_device_status(found_device, amps)
                latest_power = calc_power

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()

def get_latest_power():
    return latest_power

def get_device_id():
    return device_id