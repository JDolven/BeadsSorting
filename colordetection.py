import serial
import cv2
import threading
import time
import logging
import numpy as np
from flask import Flask, request, jsonify, Response, render_template
import random

app = Flask(__name__)

# Initialize serial communication
ser = serial.Serial('COM4', 9600, timeout=1)

# Global flag for color detection and testing status
color_detection_active = False
color_detection_thread = None
test_active = False

# Initialize camera
camera = cv2.VideoCapture(0)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Color ranges for identification (example values)
color_ranges = {
    "box_1": ([0, 100, 100], [10, 255, 255], "Red"),          # Red
    "box_2": ([36, 100, 100], [86, 255, 255], "Green"),       # Green
    "box_3": ([94, 80, 2], [126, 255, 255], "Blue"),          # Blue
    "box_4": ([15, 100, 100], [35, 255, 255], "Yellow"),      # Yellow
    "box_5": ([25, 100, 100], [35, 255, 255], "Light Green"), # Light Green
    "box_6": ([130, 100, 100], [170, 255, 255], "Purple"),    # Purple
    "box_7": ([0, 0, 100], [10, 50, 255], "Brown"),           # Brown
    "box_8": ([5, 50, 50], [15, 255, 255], "Orange"),         # Orange
    "box_9": ([0, 0, 0], [255, 255, 50], "Black"),            # Black
    "box_10": ([0, 0, 200], [255, 50, 255], "White"),         # White
    "box_11": ([100, 100, 100], [140, 255, 255], "Sky Blue"), # Sky Blue
    "box_12": ([75, 100, 100], [85, 255, 255], "Turquoise"),  # Turquoise
    "box_13": ([0, 100, 50], [10, 255, 200], "Pink"),         # Pink
    "box_14": ([20, 100, 50], [30, 255, 200], "Light Yellow"),# Light Yellow
    "box_15": ([140, 100, 100], [160, 255, 255], "Violet"),   # Violet
    "box_16": ([0, 50, 50], [10, 255, 255], "Dark Red"),      # Dark Red
    "box_17": ([85, 100, 100], [95, 255, 255], "Teal"),       # Teal
    "box_18": ([0, 0, 0], [255, 255, 255], "Unknown")         # Default for unknown colors
}


def send_command(command, retries=1):
    for attempt in range(retries):
        logging.info(f"Sending command: {command} (Attempt {attempt + 1})")
        ser.write(f"{command}\n".encode('utf-8'))
        response = ser.readline().decode('utf-8').strip()
        #time.sleep(4) 
        if "ERROR" in response:
            logging.error(f"Machine reported an error: {response}")
        elif "WAITING" in response:
            logging.info(f"Received response: {response}")
            return response
         # Wait before retrying
    return "ERROR: Failed to send command after retries"


def move_to_box(box_number, color_name=None):
    return send_command(box_number)  # Send only the box number as a string

def get_machine_status():
    logging.info("Checking machine status...")
    response = ser.readline().decode().strip()
    logging.info(f"Machine status: {response}")
    return response

def clear_machine_status():
    """Clear the status after it has been processed."""
    while ser.in_waiting > 0:
        ser.readline()  # Read and discard any remaining data in the buffer
    logging.info("Machine status cleared.")

def identify_color(frame):
    # Convert the entire frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the area (ROI) where you want to check for color
    height, width = hsv_frame.shape[:2]
    center_x, center_y = width // 2, height // 2
    region_size = 100  # Define the size of the area (e.g., 100x100 pixels)

    # Extract the ROI
    roi = hsv_frame[center_y-region_size:center_y+region_size, center_x-region_size:center_x+region_size]

    # Loop through the color ranges to find a match within the ROI
    for box, (lower, upper, color_name) in color_ranges.items():
        lower_bound = tuple(lower)
        upper_bound = tuple(upper)
        mask = cv2.inRange(roi, lower_bound, upper_bound)
        if cv2.countNonZero(mask) > 0:
            box_number = box.split('_')[-1]  # Extract the box number (e.g., "1" from "box_1")
            return box_number, color_name, (center_x-region_size, center_y-region_size, center_x+region_size, center_y+region_size)

    logging.info("No matching color found, defaulting to box 18")
    return "18", "Unknown", (center_x-region_size, center_y-region_size, center_x+region_size, center_y+region_size)

def color_detection_loop():
    global color_detection_active
    
    # Move to box 1 at the start of the loop
    logging.info("Moving to box 1 at the start of color detection")

    while color_detection_active:
        # Wait for the machine to publish its status
        status = ser.readline().decode('utf-8').strip()
        logging.info(f"Received machine status: {status}")
        if status == "WAITING: Listening for next command...":
            clear_machine_status()  # Clear status after sending the command
            # Only capture a frame and move to the corresponding box when the machine is ready
            ret, frame = camera.read()
            if ret:
                box_number, color_name, _ = identify_color(frame)  # Discard the ROI coordinates
                logging.info(f"Color: {color_name}")
                move_to_box(box_number)  # Only send the box number to the machine

        # Wait a bit before checking again to avoid unnecessary load
        time.sleep(0.5)

    logging.info("Color detection loop ended.")


def test_loop():
    global test_active
    while test_active:
        status = ser.readline().decode('utf-8').strip()
        if "WAITING" in status:
            logging.info("Machine is ready, selecting a random box.")
            box_number = str(random.randint(1, 18))
            move_to_box(box_number)  # Send the randomly selected box number to the machine
            #time.sleep(2)  # Delay to simulate processing time
        else:
            logging.info(f"Received response from machine: {status}")
        time.sleep(1)  # Small delay to prevent busy-waiting

@app.route('/color_detection', methods=['POST'])
def toggle_color_detection():
    global color_detection_active, color_detection_thread
    action = request.json.get("action")

    if action == "start" and not color_detection_active:
        logging.info("Starting color detection...")

        # Move the arm to box 1 before starting the color detection loop
        move_to_box("1")

        color_detection_active = True
        color_detection_thread = threading.Thread(target=color_detection_loop)
        color_detection_thread.start()
        return jsonify({"status": "Color detection started"})
    elif action == "stop" and color_detection_active:
        logging.info("Stopping color detection...")
        color_detection_active = False
        if color_detection_thread is not None:
            color_detection_thread.join()
        return jsonify({"status": "Color detection stopped"})
    else:
        return jsonify({"status": "Invalid action or color detection already in desired state"}), 400


@app.route('/test', methods=['POST'])
def toggle_test():
    global test_active
    action = request.json.get("action")

    if action == "start" and not test_active:
        logging.info("Starting test...")
        test_active = True
        threading.Thread(target=test_loop).start()
        return jsonify({"status": "Test started"})
    elif action == "stop" and test_active:
        logging.info("Stopping test...")
        test_active = False
        return jsonify({"status": "Test stopped"})
    else:
        return jsonify({"status": "Invalid action or test already in desired state"}), 400

@app.route('/command', methods=['POST'])
def command():
    data = request.json
    cmd_type = data.get("type")
    value = data.get("value")

    if cmd_type == "DISABLE":
        response = send_command("DISABLE")
    elif cmd_type == "ENABLE":
        response = send_command("ENABLE")
    elif cmd_type == "DISK":
        response = send_command(f"DISK {value}")
    elif cmd_type == "ARM":
        response = send_command(f"ARM {value}")
    elif cmd_type == "X_STEP":
        response = send_command(f"X_STEP {value}")
    elif cmd_type == "Y_STEP":
        response = send_command(f"Y_STEP {value}")
    elif cmd_type == "MOVE_BOX":
        response = move_to_box(value)
    else:
        return jsonify({"status": "ERROR", "message": "Invalid command type"}), 400

    return jsonify({"status": "SUCCESS", "message": response})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "WAITING: Listening for next command..."})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                # Identify the color in the ROI and get the corresponding box number, color name, and ROI coordinates
                box_number, color_name, roi_coords = identify_color(frame)

                # Draw the bounding box around the ROI
                (start_x, start_y, end_x, end_y) = roi_coords
                cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (255, 255, 255), 2)

                # Display the detected box number and color name on the frame
                text = f"Box: {box_number}, Color: {color_name}"
                text_position = (start_x, start_y - 10)
                cv2.putText(frame, text, text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                # Encode the frame as a JPEG image
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Yield the frame to be displayed
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=False)
