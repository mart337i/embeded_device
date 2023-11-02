from grove_rgb_lcd import *
import requests
from datetime import datetime
import time
from typing import Optional
import logging
from dotenv import load_dotenv
_logger = logging.getLogger(__name__)

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
