import socket
import subprocess
import psutil
import serial
import time
import requests
import json
from datetime import datetime


def get_hdd_status(drive_id):
    result = subprocess.run(['smartctl', '-H', '/dev/{}'.format(drive_id)], capture_output=True, text=True)
    output = result.stdout
    return "FAIL" if "PASSED" not in output else "OK"

def get_gpu_temperature():
    temps = psutil.sensors_temperatures()
    amdgpu = temps.get('amdgpu', [])
    return str(int(amdgpu[0].current))

def get_cpu_temperature():
    temps = psutil.sensors_temperatures()
    k10temp = temps.get('k10temp', [])
    return str(int(k10temp[0].current))

def get_cpu_usage_percentage():
    try:
        # Use psutil to get CPU usage
        usage_percent = psutil.cpu_percent(interval=1)
        return str(int(usage_percent))
    except Exception as e:
        return str(e)


def get_gpu_usage_percentage():
    try:
        # Use 'amdgpu_top' with JSON output mode for a single iteration
        result = subprocess.run(['amdgpu_top', '-J', '-n', '1'], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        # Parse the JSON output
        data = json.loads(output)
        if 'devices' in data and len(data['devices']) > 0:
            device = data['devices'][0]
            if 'gpu_activity' in device and 'GFX' in device['gpu_activity']:
                usage_percent = device['gpu_activity']['GFX']['value']
                return str(usage_percent)
        return "0"  # Return 0 if no usage data found
    except Exception as e:
        return str(e)

def get_memory_usage_percentage():
    # Run the 'free' command to get memory usage information
    result = subprocess.run(['free', '-b'], capture_output=True, text=True, check=True)

    # Output of the 'free' command
    output = result.stdout

    # Extracting the line that contains memory usage information
    lines = output.splitlines()
    for line in lines:
        if line.startswith("Mem:"):
            # Splitting the line to extract the total and used memory
            parts = line.split()
            total_memory = int(parts[1])
            used_memory = int(parts[2])

            # Calculate the percentage of used memory
            return str(int((used_memory / total_memory) * 100))


def get_ping_time(destination='1.1.1.1', count=4):
    # Run the 'ping' command
    result = subprocess.run(['ping', '-c', str(count), destination], capture_output=True, text=True, check=True)

    # Output of the 'ping' command
    output = result.stdout

    # Extract the line that contains the ping statistics summary
    lines = output.splitlines()
    for line in lines:
        if 'rtt min/avg/max/mdev' in line:
            # Split the line to extract the average ping time
            parts = line.split('/')
            return str(int(float(parts[4])))

def get_external_ip():
    try:
        # Use an external service to get the public IP address
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()

        # Parse the JSON response to get the IP address
        ip_data = response.json()['ip']

        return ip_data.split(".")[0] + "." + ip_data.split(".")[1] + ".X.X"
    except requests.RequestException as e:
        return "0.0.0.0"



# Change this to the correct port for your Raspberry Pi Pico
# On Windows it might be COM3, COM4, etc.
# On macOS/Linux it might be /dev/ttyACM0
port = '/dev/ttyACM0'  # Replace with your port
baudrate = 115200  # Baudrate must match the one used by the Pico

def send_message(port, baudrate, message):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            ser.write((message + '\n').encode())
    except serial.SerialException as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    formatted_message = ""
    formatted_message += get_hdd_status("sda") + "-"
    formatted_message += get_hdd_status("sdb") + "-"
    formatted_message += get_cpu_temperature() + "-"
    formatted_message += get_gpu_temperature() + "-"
    formatted_message += get_cpu_usage_percentage() + "-"
    formatted_message += get_gpu_usage_percentage() + "-"
    formatted_message += get_memory_usage_percentage() + "-"
    formatted_message += get_external_ip() + "-"
    formatted_message += get_ping_time() + "-"
    formatted_message += "YES" + "-" ## This line has been edited for privacy
    formatted_message += datetime.now().strftime("%H:%M %d %b").upper()

    send_message(port, baudrate, formatted_message)

