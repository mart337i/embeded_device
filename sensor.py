from grove_rgb_lcd import *
import requests
from datetime import datetime
import time
from typing import Optional
import os
import json
from dotenv import load_dotenv
Serial_number = os.getenv("SERIAL_NUMBER")

import logging
_logger = logging.getLogger(__name__)

class Sensor():
    """
        At startup we create an instans of the sensor object
        this is mostly to encapulate the sensors properties in a class

        @prams: 
            serial_number : str
            name : str 
            building : int
            facility_id : int
            sensor_id : int #NOTE we only get the id from the database when it has entered the database and it has returned the request 
    """
    def __init__(self, serial_number=Serial_number,name="", building_id=1, facility_id=1, sensor_id=None):
        BASE_URL = "http://meo.local"
        self.name = requests.get(f"{BASE_URL}/get_taget_name/").content.decode()
        time.sleep(1)
        self.building_id = requests.get(f"{BASE_URL}/get_taget_building/").content.decode()
        time.sleep(1)
        self.facility_id = requests.get(f"{BASE_URL}/get_taget_facility/").content.decode()
        time.sleep(1)
        self.serial_number = serial_number

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
        _logger.warning(f"res : {response.status_code}, json {response.content}")

        if response.status_code == 500:
            while response.status_code == 500:
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
            data = json.loads(content)  # Parse the JSON string into a Python dictionary
            self.sensor_id = data["id"]  # Access the "id" value from the dictionary