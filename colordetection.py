import serial
import cv2
import threading
import time
import logging
import math
import numpy as np
from flask import Flask, request, jsonify, Response, render_template
import os  # Add this import to handle directories

app = Flask(__name__)

#Save pictures to file
Save_pictures= True

# Initialize serial communication
ser = serial.Serial('COM4', 9600, timeout=1)

# Global flag for color detection and testing status
color_detection_active = False
color_detection_thread = None

# Variables to keep track of the machine
current_arm_position = 0
steps_per_degree_arm = 8.88888  # Step calculation based on 1.8 degree stepper and 16 microsteps
steps_per_hole = 400 # Step calculation based on 1.8 degree stepper and 16 microsteps and totalt of 8 holes in disk
current_disk_position = 0


# Initialize camera
camera = cv2.VideoCapture(0)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Color ranges for identification
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
# Box position in deg for box 1 to 18 (array item 0-17)
box_positions = [
    0, 15, 30, 45, 60, 75, 90, 105, 120, 
    135, 150, 165, 180, 195, 210, 225, 240, 255
]

def create_color_directories():
    for _, _, color_name in color_ranges.values():
        directory = os.path.join("bead_images", color_name)
        if not os.path.exists(directory):
            os.makedirs(directory)

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

def move_to_box(box_number, color_name=None, frame=None, roi_coords=None):
    """Send the command to move to a box and save the cropped image."""
    response = move_arm_to_position(box_positions[box_number]-1)
    response = move_disk_to_next_hole()
    if frame is not None and color_name is not None and roi_coords is not None and Save_pictures:
        save_image(frame, color_name, roi_coords)
    return response

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

def move_arm_to_position(target_position):
    global current_arm_position
    
    movement = target_position - current_arm_position

    if movement == 0:
        print("INFO: No movement required, arm already in position.")
        return
    
    # Calculate the number of steps required for the arm to move
    steps_to_move = round(movement * steps_per_degree_arm)

    # Perform the movement
    send_command(f"Y_STEP {steps_to_move}")
    
    current_arm_position = target_position  # Update the current position
    print(f"INFO: Arm moved to {current_arm_position} degrees.")

def move_disk_to_next_hole():
    global current_disk_position
    
    # Perform the movement to the next hole
    send_command(f"X_STEP {steps_per_hole}")
    
    # Update the position (0 to 5)
    current_disk_position = (current_disk_position + 1) % 6

    print(f"INFO: Disk moved to position {current_disk_position}.")

def identify_color(frame):
    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the area (ROI) in the center of the frame
    height, width = hsv_frame.shape[:2]
    center_x, center_y = width // 2, height // 2
    region_size = 10  # Half of 20x20 region size

    # Extract the 20x20 pixel region in the center of the frame
    roi = hsv_frame[center_y - region_size:center_y + region_size, center_x - region_size:center_x + region_size]

    # Also, extract the corresponding BGR region
    roi_bgr = frame[center_y - region_size:center_y + region_size, center_x - region_size:center_x + region_size]

    # Calculate the average RGB values in the ROI
    avg_bgr = cv2.mean(roi_bgr)[:3]  # Get the BGR values
    avg_rgb = avg_bgr[::-1]  # Convert BGR to RGB

    # Log the average RGB values
    logging.info(f"Average RGB values: {avg_rgb}")

    detected_box_number = None
    detected_color_name = "Unknown"

    # Loop through the color ranges to find a match within the ROI
    for box, (lower, upper, color_name) in color_ranges.items():
        lower_bound = np.array(lower)
        upper_bound = np.array(upper)
        mask = cv2.inRange(roi, lower_bound, upper_bound)

        if cv2.countNonZero(mask) > 0:
            detected_box_number = box.split('_')[-1]  # Extract the box number
            detected_color_name = color_name
            break

    # Return the final detected box number and color name, along with the ROI coordinates
    return detected_box_number, detected_color_name, (center_x - region_size, center_y - region_size, center_x + region_size, center_y + region_size)

def color_detection_loop():
    global color_detection_active

    while color_detection_active:
        status = ser.readline().decode('utf-8').strip()
        logging.info(f"Received machine status: {status}")
        if status == "WAITING: Listening for next command...":
            clear_machine_status()  # Clear status after sending the command
            time.sleep(0.5) # Delay between movments, to prevent the arm from trowing beads.. 
            ret, frame = camera.read()
            if ret:
                box_number, color_name, roi_coords = identify_color(frame)  # Capture the ROI coordinates
                logging.info(f"Color: {color_name}")
                move_to_box(box_number, color_name, frame, roi_coords)  # Pass the frame and ROI coordinates
                
                # Introduce a delay to avoid overlapping commands
                #time.sleep(2)  # Adjust the sleep time based on the machine's response time

        # Wait a bit before checking again to avoid unnecessary load
        time.sleep(0.5)

def save_image(frame, color_name, roi_coords):
    """Save the cropped image of the ROI to the corresponding color folder."""
    directory = os.path.join("bead_images", color_name)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.jpg"
    filepath = os.path.join(directory, filename)

    # Crop the frame to the ROI
    (start_x, start_y, end_x, end_y) = roi_coords
    cropped_frame = frame[start_y-100:end_y+100, start_x-100:end_x+100]

    # Save the cropped image
    cv2.imwrite(filepath, cropped_frame)
    logging.info(f"Saved cropped image to {filepath}")

@app.route('/color_detection', methods=['POST'])
def toggle_color_detection():
    global color_detection_active, color_detection_thread
    action = request.json.get("action")

    if action == "start" and not color_detection_active:
        logging.info("Starting color detection...")

        # Move the arm to box 1 before starting the color detection loop

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
    # Call this function once at the start
    create_color_directories()
    app.run(debug=False, host='0.0.0.0', port=5000)
