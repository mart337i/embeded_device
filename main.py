import grovepi
from grove_rgb_lcd import *
import requests
from datetime import datetime
import math
import time
from typing import Optional
import logging
from dotenv import load_dotenv
import os

#Import custom
from sensor import Sensor
from sensor_type import SensorType
from sensor_value import SensorValue

# Load environment variables from .env file
load_dotenv()

# Access the serial number
serial_number = os.getenv("SERIAL_NUMBER")

#I chould properly do enums for each availabe port and thier type, but no
SENSOR_PORT = os.getenv("SENSOR_PORT")
SENSOR_TYPE = os.getenv("SENSOR_TYPE")

logging.basicConfig(filename='/home/pi/code/embeded_device/logs/app.log',  # log to a file named 'app.log'
                    filemode='a',  # append to the log file if it exists, otherwise create it
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

_logger = logging.getLogger(__name__)
BASE_URL = "http://meo.local"

#Global, this is basicly the sensor it self
global_sensor = Sensor(serial_number,name="", building_id=1, facility_id=1, sensor_id=0)

def send_alarm(message):
    url = f"{BASE_URL}/alarm/"
    data = {
        "type": "failure",
        "message": message,
        "serial_number" : global_sensor.serial_number
    }
    response = requests.post(url, json=data)
    if response.status_code != 200:
        _logger.warning(f"Alarm sent: {response.status_code}, {response.text}")
    else:
        _logger.info(f"Alarm sent: {response.status_code}, {response.text}")

def get_temp_humidity():
    try:
        [temp, humidity] = grovepi.dht(SENSOR_PORT, SENSOR_TYPE)
        
        if not (math.isnan(temp) or math.isnan(humidity)):
            setText(f"Temp : {temp}.\nhum: {humidity}")
            _logger.info(f"Temp : {temp}. hum: {humidity}")
            return temp, humidity
        else:
            _logger.warning(f"raw temp val : {temp}. raw humidity: {humidity}")
            return None, None

    except IOError as e:
        send_alarm(f"Error with GrovePi sensor: {e}")
        return None, None

def post_temp_humidity_data(sensorValue: SensorValue = None, sensor: Sensor = global_sensor):
    url = f"{BASE_URL}/sensor_value/"

    temperature, humidity = get_temp_humidity()
    if not temperature or not humidity:
        _logger.error(f"value not set for either temperature : {temperature} or humidity: {humidity}")
        return

    data = {
        "sensorType": SensorType.TEMPERATURE.value,
        "value": temperature,
        "value_datetime": datetime.utcnow().isoformat(),
        "sensor_id": sensor.sensor_id
    }

    response = requests.post(url, json=data)
    if response.status_code != 200:
        time.sleep(10)
        _logger.error(f"Error while posting to api. Status code {response.status_code}")
        return
    _logger.info(f"Posted temperature to API: {response.status_code}, {response.text}")

    data = {
        "sensorType": SensorType.HUMIDITY.value,
        "value": humidity,
        "value_datetime": datetime.utcnow().isoformat(),
        "sensor_id": sensor.sensor_id
    }

    response = requests.post(url, json=data)
    if response.status_code != 200:
        time.sleep(10)
        _logger.error(f"Error while posting to api. Status code {response.status_code}")
        return
    
    _logger.info(f"Posted humidity to API: {response.status_code}, {response.text}")

 
def main():
    _logger.info("Application has loaded, starting main procsess<")
    _logger.info(f"Sensor created : {global_sensor.__dict__}")
    if global_sensor.sensor_id == 0:
        return exit(-1)
    
    while True:
        time.sleep(10)
        post_temp_humidity_data(global_sensor)

main()