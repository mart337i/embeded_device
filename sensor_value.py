from datetime import datetime
from sensor_type import SensorType

class SensorValue:
    """ Class here for consistency 
    
    """
    def __init__(self, sensorType=SensorType.TEMPERATURE, value=0, value_datetime=datetime.utcnow().isoformat(), sensor_id=None):
        self.id = None
        self.sensorType = sensorType
        self.value = value
        self.value_datetime = value_datetime
        self.sensor_id = sensor_id