import serial
import time

# Initialize serial communication with Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

# Define the color ranges and corresponding color names
color_ranges = {
    "red": [(0, 120, 70), (10, 255, 255)],
    "green": [(40, 40, 40), (70, 255, 255)],
    "blue": [(90, 50, 50), (130, 255, 255)],
    "yellow": [(20, 100, 100), (30, 255, 255)],
    "orange": [(10, 100, 20), (25, 255, 255)],
    "purple": [(130, 50, 50), (160, 255, 255)],
    "pink": [(160, 50, 50), (170, 255, 255)],
    "cyan": [(80, 100, 100), (90, 255, 255)],
    "magenta": [(140, 100, 100), (160, 255, 255)],
    "brown": [(10, 100, 20), (20, 150, 150)],
    "black": [(0, 0, 0), (180, 255, 50)],
    "white": [(0, 0, 200), (180, 20, 255)],
    "gray": [(0, 0, 100), (180, 50, 200)],
    "gold": [(20, 150, 150), (30, 255, 255)],
    "silver": [(0, 0, 160), (180, 10, 200)],
    "turquoise": [(80, 200, 200), (90, 255, 255)],
    "navy": [(100, 100, 100), (120, 255, 255)],
    "unknown": [(0, 0, 0), (180, 255, 255)]  # Default to unknown if nothing matches
}

def detect_color(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color_name, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
        if cv2.countNonZero(mask) > 0:
            return color_name
    return "unknown"

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()

        if line == "CHECK_COLOR":
            # Capture frame from the camera (assuming camera setup is done)
            ret, frame = cap.read()  # Assuming cap is your cv2.VideoCapture object
            if not ret:
                ser.write(b"unknown\n")
                continue

            color = detect_color(frame)
            ser.write((color + "\n").encode('utf-8'))

        elif line == "CHECK_ALIGNMENT":
            # Handle alignment check
            # Respond with "ROTOR_ALIGNED" or "NOT_ALIGNED" as needed
            alignment_status = "ROTOR_ALIGNED"  # Placeholder for actual alignment logic
            ser.write((alignment_status + "\n").encode('utf-8'))
