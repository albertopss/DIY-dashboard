def hex_to_int(hex_str):
    """Convert a hexadecimal string to an integer."""
    return int(hex_str, 16)

def maf(code):
    """Calculate Mass Air Flow (MAF) from the code."""
    code = hex_to_int(code)
    return code * 0.00132276

def throttle_pos(code):
    """Calculate Throttle Position from the code."""
    code = hex_to_int(code)
    return code * 100.0 / 255.0

def intake_m_pres(code):
    """Calculate Intake Manifold Pressure in kPa from the code."""
    code = hex_to_int(code)
    return code / 0.14504

def rpm(code):
    """Calculate RPM from the code."""
    code = hex_to_int(code)
    return code / 4

def speed(code):
    """Calculate Vehicle Speed from the code."""
    code = hex_to_int(code)
    return code / 1.609

def percent_scale(code):
    """Convert a code to a percentage scale."""
    code = hex_to_int(code)
    return code * 100.0 / 255.0

def timing_advance(code):
    """Calculate Timing Advance from the code."""
    code = hex_to_int(code)
    return (code - 128) / 2.0

def sec_to_min(code):
    """Convert seconds to minutes from the code."""
    code = hex_to_int(code)
    return code / 60

def temp(code):
    """Calculate temperature in Fahrenheit from the code."""
    code = hex_to_int(code)
    celsius = code - 40
    return 32 + (9 * celsius / 5)

def cpass(code):
    """Pass-through function (no processing)."""
    return code

def fuel_trim_percent(code):
    """Calculate fuel trim percentage from the code."""
    code = hex_to_int(code)
    return (code - 128) * 100 / 128

def dtc_decrypt(code):
    """Decrypt Diagnostic Trouble Codes (DTC) from the code."""
    num = hex_to_int(code[:2])
    res = []
    
    mil = 1 if num & 0x80 else 0
    num &= 0x7F
    res.append(num)
    res.append(mil)

    numB = hex_to_int(code[2:4])
    res.extend([((numB >> i) & 0x01) + ((numB >> (3 + i)) & 0x02) for i in range(3)])

    numC = hex_to_int(code[4:6])
    numD = hex_to_int(code[6:8])
    
    res.extend([((numC >> i) & 0x01) + (((numD >> i) & 0x01) << 1) for i in range(7)])
    res.append((numD >> 7) & 0x01)  # EGR System C7 bit
    
    return "#"

def hex_to_bitstring(hex_str):
    """Convert a hexadecimal string to a bitstring."""
    bitstring = ""
    for char in hex_str:
        if isinstance(char, str):  # Ensure type safety
            v = int(char, 16)
            bitstring += ''.join('1' if v & (1 << i) else '0' for i in range(4))
    return bitstring

class Sensor:
    def __init__(self, short_name, sensor_name, sensor_command, sensor_value_function, unit):
        self.shortname = short_name
        self.name = sensor_name
        self.cmd = sensor_command
        self.value = sensor_value_function
        self.unit = unit

SENSORS = [
    Sensor("pids", "Supported PIDs", "0100", hex_to_bitstring, ""),
    Sensor("dtc_status", "S-S DTC Cleared", "0101", dtc_decrypt, ""),
    Sensor("dtc_ff", "DTC C-F-F", "0102", cpass, ""),
    Sensor("fuel_status", "Fuel System Stat", "0103", cpass, ""),
    Sensor("load", "Calc Load Value", "0104", percent_scale, ""),
    Sensor("temp", "Coolant Temp", "0105", temp, "F"),
    Sensor("short_term_fuel_trim_1", "S-T Fuel Trim", "0106", fuel_trim_percent, "%"),
    Sensor("long_term_fuel_trim_1", "L-T Fuel Trim", "0107", fuel_trim_percent, "%"),
    Sensor("short_term_fuel_trim_2", "S-T Fuel Trim", "0108", fuel_trim_percent, "%"),
    Sensor("long_term_fuel_trim_2", "L-T Fuel Trim", "0109", fuel_trim_percent, "%"),
    Sensor("fuel_pressure", "FuelRail Pressure", "010A", cpass, ""),
    Sensor("manifold_pressure", "Intk Manifold", "010B", intake_m_pres, "psi"),
    Sensor("rpm", "Engine RPM", "010C", rpm, ""),
    Sensor("speed", "Vehicle Speed", "010D", speed, "MPH"),
    Sensor("timing_advance", "Timing Advance", "010E", timing_advance, "degrees"),
    Sensor("intake_air_temp", "Intake Air Temp", "010F", temp, "F"),
    Sensor("maf", "AirFlow Rate(MAF)", "0110", maf, "lb/min"),
    Sensor("throttle_pos", "Throttle Position", "0111", throttle_pos, "%"),
    Sensor("secondary_air_status", "2nd Air Status", "0112", cpass, ""),
    Sensor("o2_sensor_positions", "Loc of O2 sensors", "0113", cpass, ""),
    Sensor("o211", "O2 Sensor: 1 - 1", "0114", fuel_trim_percent, "%"),
    Sensor("o212", "O2 Sensor: 1 - 2", "0115", fuel_trim_percent, "%"),
    Sensor("o213", "O2 Sensor: 1 - 3", "0116", fuel_trim_percent, "%"),
    Sensor("o214", "O2 Sensor: 1 - 4", "0117", fuel_trim_percent, "%"),
    Sensor("o221", "O2 Sensor: 2 - 1", "0118", fuel_trim_percent, "%"),
    Sensor("o222", "O2 Sensor: 2 - 2", "0119", fuel_trim_percent, "%"),
    Sensor("o223", "O2 Sensor: 2 - 3", "011A", fuel_trim_percent, "%"),
    Sensor("o224", "O2 Sensor: 2 - 4", "011B", fuel_trim_percent, "%"),
    Sensor("obd_standard", "OBD Designation", "011C", cpass, ""),
    Sensor("o2_sensor_position_b", "Loc of O2 sensor", "011D", cpass, ""),
    Sensor("aux_input", "Aux input status", "011E", cpass, ""),
    Sensor("engine_time", "Engine Start MIN", "011F", sec_to_min, "min"),
    Sensor("engine_mil_time", "Engine Run MIL", "014D", sec_to_min, "min"),
]

def test():
    """Test function to print sensor values."""
    for sensor in SENSORS:
        print(sensor.name, sensor.value("F"))

if __name__ == "__main__":
    test()

