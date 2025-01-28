import serial
import string
import time
from math import ceil
from datetime import datetime
import obd_sensors
from obd_sensors import hex_to_int
from debugEvent import debug_display

# Command constants
GET_DTC_COMMAND = "03"
CLEAR_DTC_COMMAND = "04"
GET_FREEZE_DTC_COMMAND = "07"

# Function to decrypt DTC code
def decrypt_dtc_code(code):
    """Returns the 5-digit DTC code from hex encoding."""
    dtc = []
    current = code
    for i in range(0, 3):
        if len(current) < 4:
            raise ValueError(f"Tried to decode bad DTC: {code}")

        tc = hex_to_int(current[0])  # type code
        tc >>= 2
        
        if tc == 0:
            type_code = "P"
        elif tc == 1:
            type_code = "C"
        elif tc == 2:
            type_code = "B"
        elif tc == 3:
            type_code = "U"
        else:
            raise ValueError(f"Invalid type code: {tc}")

        dig1 = str(hex_to_int(current[0]) & 3)
        dig2 = str(hex_to_int(current[1]))
        dig3 = str(hex_to_int(current[2]))
        dig4 = str(hex_to_int(current[3]))
        dtc.append(type_code + dig1 + dig2 + dig3 + dig4)
        current = current[4:]
    return dtc

class OBDPort:
    """OBDPort abstracts all communication with OBD-II device."""
    def __init__(self, portnum, _notify_window, SERTIMEOUT, RECONNATTEMPTS):
        """Initializes port by resetting device and getting supported PIDs."""
        baud = 38400
        databits = 8
        par = serial.PARITY_NONE  # parity
        sb = 1  # stop bits
        to = SERTIMEOUT
        self.ELMver = "Unknown"
        self.State = 1  # state SERIAL is 1 connected, 0 disconnected (connection failed)
        self.port = None
        
        self._notify_window = _notify_window
        debug_display(self._notify_window, 1, "Opening interface (serial port)")

        try:
            self.port = serial.Serial(portnum, baud, parity=par, stopbits=sb, bytesize=databits, timeout=to)
        except serial.SerialException as e:
            print(e)
            self.State = 0
            return
        
        debug_display(self._notify_window, 1, f"Interface successfully {self.port.portstr} opened")
        debug_display(self._notify_window, 1, "Connecting to ECU...")

        try:
            self.send_command("atz")  # initialize
            time.sleep(1)
        except serial.SerialException:
            self.State = 0
            return
        
        self.ELMver = self.get_result()
        if self.ELMver is None:
            self.State = 0
            return
        
        debug_display(self._notify_window, 2, f"atz response: {self.ELMver}")
        self.send_command("ate0")  # echo off
        debug_display(self._notify_window, 2, f"ate0 response: {self.get_result()}")
        self.send_command("0100")
        ready = self.get_result()
        
        if ready is None:
            self.State = 0
            return
        
        debug_display(self._notify_window, 2, f"0100 response: {ready}")
    
    def close(self):
        """Resets device and closes all associated filehandles."""
        if self.port is not None and self.State == 1:
            self.send_command("atz")
            self.port.close()
        
        self.port = None
        self.ELMver = "Unknown"

    def send_command(self, cmd):
        """Internal use only: not a public interface."""
        if self.port:
            self.port.flushOutput()
            self.port.flushInput()
            self.port.write((cmd + "\r\n").encode('utf-8'))

    def interpret_result(self, code):
        """Internal use only: not a public interface."""
        if len(code) < 7:
            print("boguscode? " + code)
            return None
        
        code = code.split("\r")[0]  # get the first part of the response
        code = ''.join(code.split())  # remove whitespace
        
        if code.startswith("NODATA"):  # there is no such sensor
            return "NODATA"
        
        code = code[4:]  # first 4 characters are code from ELM
        return code
    
    def get_result(self):
        """Internal use only: not a public interface."""
        repeat_count = 0
        if self.port is not None:
            buffer = ""
            while True:
                c = self.port.read(1).decode('utf-8')
                if len(c) == 0:
                    if repeat_count == 5:
                        break
                    print("Got nothing\n")
                    repeat_count += 1
                    continue
                
                if c == '\r':
                    continue
                
                if c == ">":
                    break
                    
                if buffer or c != ">":  # if something is in buffer, add everything
                    buffer += c
            
            if buffer == "":
                return None
            return buffer
        else:
            debug_display(self._notify_window, 3, "NO self.port!")
        return None

    def get_sensor_value(self, sensor):
        """Internal use only: not a public interface."""
        cmd = sensor.cmd
        self.send_command(cmd)
        data = self.get_result()
        
        if data:
            data = self.interpret_result(data)
            if data != "NODATA":
                data = sensor.value(data)
        else:
            return "NORESPONSE"
        
        return data

    def sensor(self, sensor_index):
        """Returns 3-tuple of given sensors. 3-tuple consists of
        (Sensor Name (string), Sensor Value (string), Sensor Unit (string) )"""
        sensor = obd_sensors.SENSORS[sensor_index]
        r = self.get_sensor_value(sensor)
        return (sensor.name, r, sensor.unit)

    def sensor_names(self):
        """Internal use only: not a public interface."""
        return [s.name for s in obd_sensors.SENSORS]

    def get_tests_MIL(self):
        statusText = ["Unsupported", "Supported - Completed", "Unsupported", "Supported - Incompleted"]
        
        statusRes = self.sensor(1)[1]  # GET values
        statusTrans = []  # translate values to text
        
        statusTrans.append(str(statusRes[0]))  # DTCs
        
        if statusRes[1] == 0:  # MIL
            statusTrans.append("Off")
        else:
            statusTrans.append("On")
        
        for i in range(2, len(statusRes)):  # Tests
            statusTrans.append(statusText[statusRes[i]])
        
        return statusTrans

    def get_dtc(self):
        """Returns a list of all pending DTC codes. Each element consists of
        a 2-tuple: (DTC code (string), Code description (string) )"""
        dtcLetters = ["P", "C", "B", "U"]
        r = self.sensor(1)[1]  # data
        dtcNumber = r[0]
        mil = r[1]
        DTCCodes = []
        
        print(f"Number of stored DTC: {dtcNumber} MIL: {mil}")
        # get all DTC, 3 per message response
        for i in range(0, ceil(dtcNumber / 3)):
            self.send_command(GET_DTC_COMMAND)
            res = self.get_result()
            print("DTC result:" + res)
            for j in range(0, 3):
                val1 = hex_to_int(res[3 + j * 6:5 + j * 6])
                val2 = hex_to_int(res[6 + j * 6:8 + j * 6])  # get DTC codes from response (3 DTC each 2 bytes)
                val = (val1 << 8) + val2  # DTC val as int
                
                if val == 0:  # skip fill of last packet
                    break
                   
                DTCStr = dtcLetters[(val & 0xC000) >> 14] + str((val & 0x3000) >> 12) + str((val & 0x0F00) >> 8) + str((val & 0x00F0) >> 4) + str(val & 0x000F)
                DTCCodes.append(["Active", DTCStr])
        
        # read mode 7
        self.send_command(GET_FREEZE_DTC_COMMAND)
        res = self.get_result()
        
        if res.startswith("NODATA"):  # no freeze frame
            return DTCCodes
        
        print("DTC freeze result:" + res)
        for i in range(0, 3):
            val1 = hex_to_int(res[3 + i * 6:5 + i * 6])
            val2 = hex_to_int(res[6 + i * 6:8 + i * 6])  # get DTC codes from response (3 DTC each 2 bytes)
           

