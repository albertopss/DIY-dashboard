import obd

# Create a connection to the OBD-II interface (e.g., USB or Bluetooth)
connection = obd.OBD()  # Automatically connects to the first available OBD-II port

# Define a function to read and display OBD data
def read_obd_data():
    # Define a list of commands you might want to read
    commands = [
        obd.commands.RPM,        # Engine RPM
        obd.commands.SPEED,      # Vehicle Speed
        obd.commands.THROTTLE_POS,  # Throttle Position
        obd.commands.COOLANT_TEMP,  # Coolant Temperature
    ]
    
    # Read and print the values for each command
    for command in commands:
        response = connection.query(command)
        
        if response.value is not None:
            print(f"{command.name}: {response.value}")
        else:
            print(f"{command.name}: No data")

if __name__ == "__main__":
    read_obd_data()
