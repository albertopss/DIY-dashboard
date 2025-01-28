import serial

def scan_serial():
    """Scan for available serial ports. Return a list of serial names."""
    available = []
    
    # Enable Bluetooth connection
    for i in range(10):
        try:
            s = serial.Serial(f"/dev/rfcomm{i}")
            available.append(str(s.portstr))
            s.close()  # Explicit close to avoid delayed GC issues
        except serial.SerialException:
            pass

    # Enable USB connection
    for i in range(256):
        try:
            s = serial.Serial(f"/dev/ttyUSB{i}")
            available.append(s.portstr)
            s.close()  # Explicit close to avoid delayed GC issues
        except serial.SerialException:
            pass

    # Enable OBD simulator (commented out for now)
    # for i in range(256):
    #     try:  # Scan Simulator
    #         s = serial.Serial(f"/dev/pts/{i}")
    #         available.append(s.portstr)
    #         s.close()  # Explicit close to avoid delayed GC issues
    #     except serial.SerialException:
    #         pass

    return available

