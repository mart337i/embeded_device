import grovepi
from grove_rgb_lcd import *
import requests
from datetime import datetime
import math
import time
from typing import Optional
from enum import Enum
import logging
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the serial number
serial_number = os.getenv("SERIAL_NUMBER")


logging.basicConfig(filename='/home/pi/code/embeded_device/logs/app.log',  # log to a file named 'app.log'
                    filemode='a',  # append to the log file if it exists, otherwise create it
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

_logger = logging.getLogger(__name__)
BASE_URL = "http://meo.local"

class Sensor():
    """
        At startup we create an instans of the sensor object
        this is mostly to encapulate the sensors properties in a class

        @prams: 
            name : str 
            building : int
            facility_id : int
            sensor_id : int #NOTE we only get the id from the database when it has entered the database and it has returned the request 
    """
    def __init__(self, serial_number,name="", building_id=1, facility_id=1, sensor_id=None):
        BASE_URL = "http://meo.local"
        self.name = requests.get(f"{BASE_URL}/get_taget_name/").content.decode()
        time.sleep(1)
        self.building_id = requests.get(f"{BASE_URL}/get_taget_building/").content.decode()
        time.sleep(1)
        self.facility_id = requests.get(f"{BASE_URL}/get_taget_facility/").content.decode()
        time.sleep(1)

        if not self.name or not self.building_id:
            _logger.warning(f"name : {self.name} or building {self.building_id}")
            exit(-1)

        sensor_data = {
            "serial_number" : serial_number,
            "name": self.name,
            "building_id": self.building_id,
        }

        _logger.warning(sensor_data)
        
        url = f"{BASE_URL}/create_sensor/"
        response = requests.post(url, json=sensor_data)
        _logger.warning(f"res : {response}, json {sensor_data}")

        # 200 OK
        # 201 Created
        # 202 Accepted
        # 203 Non-Authoritative Information
        # 204 No Content
        # 205 Reset Content
        # 206 Partial Content
        if response.status_code == 200: 
            content = response.content.decode()
            self.sensor_id = content.find("id")


class SensorType(Enum):
    """ Class here for consistency 
    
    """
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

class SensorValue:
    """ Class here for consistency 
    
    """
    def __init__(self, sensorType=SensorType.TEMPERATURE.value, value=0, value_datetime=datetime.utcnow().isoformat(), sensor_id=None,low_value = 0, max_value=100):
        self.id: int = None 
        self.sensorType: SensorType = sensorType
        self.max_value_temp: int = max_value
        self.low_value_temp: int = low_value
        self.value: float = value
        self.value_datetime: datetime = value_datetime
        self.sensor_id: int = sensor_id


#I chould properly do enums for each availabe port and thier type, but no
SENSOR_PORT = 7
SENSOR_TYPE = 0

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
        "max_value_temp": 100,
        "low_value_temp": 0,
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
        "max_value": 100,
        "low_value": 0,
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