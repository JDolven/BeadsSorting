import serial
import cv2
import threading
import time
import logging
import numpy as np
from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__)

# Initialize serial communication
ser = serial.Serial('COM4', 9600, timeout=1)

# Global flag for color detection status
color_detection_active = False
color_detection_thread = None

# Initialize camera
camera = cv2.VideoCapture(0)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Color ranges for identification (example values)
color_ranges = {
    "box_1": ([0, 100, 100], [10, 255, 255], "Red"),    # Example range for Red
    "box_2": ([36, 100, 100], [86, 255, 255], "Green"), # Example range for Green
    "box_3": ([94, 80, 2], [126, 255, 255], "Blue"),    # Example range for Blue
    # Add other color ranges here
    "box_18": ([0, 0, 0], [255, 255, 255], "Unknown")   # Default for unknown colors
}


def send_command(command, retries=3):
    for attempt in range(retries):
        logging.info(f"Sending command: {command} (Attempt {attempt + 1})")
        ser.write(f"{command}\n".encode('utf-8'))
        response = ser.readline().decode('utf-8').strip()
        if "ERROR" in response:
            logging.error(f"Machine reported an error: {response}")
        elif "WAITING" in response:
            logging.info(f"Received response: {response}")
            return response
        time.sleep(2)  # Wait before retrying
    return "ERROR: Failed to send command after retries"


def move_to_box(box_number, color_name=None):
    #logging.info(f"Moving to box: {box_number}")
    return send_command(box_number)  # Send only the box number as a string

def get_machine_status():
    logging.info("Checking machine status...")
    ser.write("STATUS\n".encode())  # Replace with actual command if necessary
    response = ser.readline().decode().strip()
    logging.info(f"Machine status: {response}")
    return response

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
            #logging.info(f"Detected color for box {box_number}: {color_name}")
            # Return the box number, color name, and ROI coordinates
            return box_number, color_name, (center_x-region_size, center_y-region_size, center_x+region_size, center_y+region_size)

    logging.info("No matching color found, defaulting to box 18")
    # Return default values along with the ROI coordinates
    return "18", "Unknown", (center_x-region_size, center_y-region_size, center_x+region_size, center_y+region_size)



def color_detection_loop():
    global color_detection_active
    while color_detection_active:
        status = get_machine_status()
        if status == "WAITING: Listening for next command...":
            ret, frame = camera.read()
            if ret:
                box_number, color_name, _ = identify_color(frame)  # Discard the ROI coordinates
                move_to_box(box_number)  # Only send the box number to the machine
                time.sleep(2)  # Increase delay to 2 seconds
        else:
            time.sleep(0.5)  # Polling interval when the machine is not waiting

    logging.info("Color detection loop ended.")


@app.route('/color_detection', methods=['POST'])
def toggle_color_detection():
    global color_detection_active, color_detection_thread
    action = request.json.get("action")

    if action == "start" and not color_detection_active:
        logging.info("Starting color detection...")
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
