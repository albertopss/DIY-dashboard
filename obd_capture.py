#!/usr/bin/env python3

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
from obd_utils import scan_serial

class OBD_Capture:
    def __init__(self):
        self.supportedSensorList = []
        self.port = None

    def connect(self):
        portnames = scan_serial()
        print(portnames)
        
        for port in portnames:
            self.port = obd_io.OBDPort(port, None, 2, 2)
            if self.port.State == 0:
                self.port.close()
                self.port = None
            else:
                print(f"Connected to {self.port.port.name}")
                return
        
        print("No available OBD port found.")

    def is_connected(self):
        return self.port is not None

    def get_supported_sensor_list(self):
        return self.supportedSensorList 

    def capture_data(self):
        if self.port is None:
            print("No connection to OBD port.")
            return None

        # Get supported sensors
        self.supp = self.port.sensor(0)[1]
        self.supportedSensorList = []
        self.unsupportedSensorList = []

        for i in range(len(self.supp)):
            if self.supp[i] == "1":
                self.supportedSensorList.append((i + 1, obd_sensors.SENSORS[i + 1]))
            else:
                self.unsupportedSensorList.append((i + 1, obd_sensors.SENSORS[i + 1]))

        for supportedSensor in self.supportedSensorList:
            print(f"Supported sensor index = {supportedSensor[0]} {supportedSensor[1].shortname}")

        time.sleep(3)
        
        # Capture data
        results = {}
        localtime = datetime.now()
        current_time = localtime.strftime("%H:%M:%S.%f")[:-3]
        text = f"{current_time}\n"

        for supportedSensor in self.supportedSensorList:
            sensorIndex = supportedSensor[0]
            name, value, unit = self.port.sensor(sensorIndex)
            text += f"{name} = {value} {unit}\n"

        return text

if __name__ == "__main__":
    o = OBD_Capture()
    o.connect()
    time.sleep(3)

    if not o.is_connected():
        print("Not connected")
    else:
        data = o.capture_data()
        print(data if data else "No data captured.")

