import grovepi
from grove_rgb_lcd import *
import requests
from datetime import datetime
import math
import time
from typing import Optional
from enum import Enum
import logging

logging.basicConfig(filename='logs/app.log',  # log to a file named 'app.log'
                    filemode='a',  # append to the log file if it exists, otherwise create it
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
_logger = logging.getLogger(__name__)
BASE_URL = "http://meo.local"


class Sensor(BASE_URL):
    """
        At startup we create an instans of the sensor object
        this is mostly to encapulate the sensors properties in a class

        @prams: 
            name : str 
            building : int
            facility_id : int
            sensor_id : int #NOTE we only get the id from the database when it has entered the database and it has returned the request 
    """
    def __init__(self, name="", building_id=1, facility_id=1, sensor_id=None):
        self.name = requests.get(f"{BASE_URL}/get_target_name/")
        self.building_id = requests.get(f"{BASE_URL}/get_target_building/")
        self.facility_id = requests.get(f"{BASE_URL}/get_target_facility/")
        sensor_data = {
            "name": self.name,
            "building_id": self.building_id
        }
        
        url = f"{BASE_URL}/sensor/"
        response = requests.post(url, json=sensor_data)

        # 200 OK
        # 201 Created
        # 202 Accepted
        # 203 Non-Authoritative Information
        # 204 No Content
        # 205 Reset Content
        # 206 Partial Content
        if response.status_code == 200: 
            content = response.content.decode()
            self.sensor_id = content["id"]
        else:
            self.sensor_id = None


class SensorType(Enum):
    """ Class here for consistency 
    
    """
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

class SensorValue:
    """ Class here for consistency 
    
    """
    id: int = None # id is null until its returned from the database
    type: SensorType
    max_value: int
    low_value: int
    value: float
    datetime: str
    sensor_id: int


#I chould properly do enums for each availabe port and thier type, but no
SENSOR_PORT = 7
SENSOR_TYPE = 0

#Global, this is basicly the sensor it self
global_sensor = Sensor(name="", building_id=1, facility_id=1, sensor_id=0)

def send_alarm(message):
    url = f"{BASE_URL}/alarm/"
    data = {
        "type": "failure",
        "message": message,
        "sonor_id" : global_sensor.sensor_id
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
    url = f"{Sensor.BASE_URL}/sensor_value/"

    temperature, humidity = get_temp_humidity()
    if not temperature or not humidity:
        _logger.error(f"value not set for either temperature : {temperature} or humidity: {humidity}")
        return

    # Creating temperature data instance
    temp_data = SensorValue(
        type=SensorType.TEMPERATURE,
        value=temperature,
        datetime=datetime.utcnow().isoformat(),
        sensor_id=sensor.sensor_id,
        max_value=100, 
        low_value=0
    )

    data = {
        "name": sensor.name,
        "sensor_value": temp_data.__dict__,
        "building_id": sensor.building_id
    }

    response = requests.post(url, json=data)
    _logger.info(f"Posted temperature to API: {response.status_code}, {response.text}")

    # Creating humidity data instance
    humidity_data = SensorValue(
        type=SensorType.HUMIDITY,
        value=humidity,
        datetime=datetime.utcnow().isoformat(),
        sensor_id=sensor.sensor_id,
        max_value=100,
        low_value=0
    )

    data["sensor_value"] = humidity_data.__dict__

    response = requests.post(url, json=data)
    _logger.info(f"Posted humidity to API: {response.status_code}, {response.text}")

 
def main():
    _logger.info("Starting application")
    if global_sensor.sensor_id == 0:
        return exit(-1)
    
    while True:
        time.sleep(1)
        post_temp_humidity_data()

if __name__ == "__main__":
    main()