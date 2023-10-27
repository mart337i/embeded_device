import grovepi
import requests
from datetime import datetime
import math

BASE_URL = "http://your_api_base_url/"

SENSOR_PORT = 4  # Assuming you have connected the DHT sensor to port D4
SENSOR_TYPE = 0  # use 1 if you have the white-colored sensor

def get_temp_humidity():
    try:
        [temp, humidity] = grovepi.dht(SENSOR_PORT, SENSOR_TYPE)

        if not (math.isnan(temp) or math.isnan(humidity)):
            return temp, humidity
        else:
            return None, None

    except IOError as e:
        send_alarm(f"Error with GrovePi sensor: {e}")
        return None, None

def post_temp_humidity_data():
    url = f"{BASE_URL}/temp-humidity-sensors/"

    temperature, humidity = get_temp_humidity()
    if not temperature or not humidity:
        return

    data = {
        "type": "temperature",
        "value": temperature,
        "name": "GrovePiTempSensor",
        "datetime": datetime.utcnow().isoformat()
    }

    response = requests.post(url, json=data)
    print(f"Posted temperature to API: {response.status_code}, {response.text}")

    data["type"] = "humidity"
    data["value"] = humidity
    data["name"] = "GrovePiHumiditySensor"

    response = requests.post(url, json=data)
    print(f"Posted humidity to API: {response.status_code}, {response.text}")

def send_alarm(message):
    url = f"{BASE_URL}/alarm/"
    data = {
        "type": "failure",
        "message": message
    }
    response = requests.post(url, json=data)
    print(f"Alarm sent: {response.status_code}, {response.text}")
