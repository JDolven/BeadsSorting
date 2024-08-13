from flask import Flask, render_template, request, jsonify
import serial
import threading
import time
import cv2
import numpy as np

app = Flask(__name__)

# Initialize serial communication with the machine
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

# Initialize the camera (assuming it's connected)
cap = cv2.VideoCapture(0)

# Shared data variables
serial_data = []
running = False

# Define the color ranges and corresponding color names (as in the previous script)
# ...

def detect_color(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color_name, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
        if cv2.countNonZero(mask) > 0:
            return color_name
    return "unknown"

def send_command(command):
    """Send a command to the machine and wait for the response."""
    ser.write(f"{command}\n".encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    return response

def handle_machine_status(response):
    """Handle the machine's response and store it."""
    serial_data.append(response)
    if "INFO" in response:
        return True  # Machine is in a good state
    elif "WAITING" in response:
        return True  # Machine is ready for the next command
    elif "ERROR" in response:
        return False  # Error occurred
    else:
        return False  # Unknown response

def machine_control():
    global running
    while running:
        response = ser.readline().decode('utf-8').strip()
        if handle_machine_status(response):
            # Capture frame from the camera
            ret, frame = cap.read()
            if not ret:
                continue  # Skip iteration if frame capture fails

            # Detect color
            color = detect_color(frame)
            box_number = color_to_box.get(color, 18)  # Default to box 18 for unknown colors

            # Send the box number command to the machine
            response = send_command(f"{box_number}")
            handle_machine_status(response)

@app.route('/')
def index():
    return render_template('index.html', serial_data=serial_data)

@app.route('/start', methods=['POST'])
def start():
    global running
    if not running:
        running = True
        threading.Thread(target=machine_control).start()
    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST'])
def stop():
    global running
    running = False
    return jsonify({"status": "stopped"})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"running": running, "serial_data": serial_data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
