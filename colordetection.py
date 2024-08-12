import cv2
import numpy as np
import serial

# Initialize serial communication (adjust "/dev/ttyS0" and baudrate as needed)
ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)
ser.flush()

# Define color ranges in HSV
color_ranges = {
    "red": [(0, 120, 70), (10, 255, 255), (170, 120, 70), (180, 255, 255)],
    "green": [(40, 40, 40), (70, 255, 255)],
    "blue": [(90, 50, 50), (130, 255, 255)],
    "yellow": [(20, 100, 100), (30, 255, 255)],
    "orange": [(10, 100, 20), (25, 255, 255)],
    "purple": [(130, 50, 50), (160, 255, 255)],
    "pink": [(160, 50, 50), (170, 255, 255)],
    "cyan": [(80, 100, 100), (90, 255, 255)],
    "brown": [(10, 100, 20), (20, 150, 150)],
    "white": [(0, 0, 200), (180, 20, 255)],
    "black": [(0, 0, 0), (180, 255, 50)]
}

def detect_color(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color, ranges in color_ranges.items():
        for (lower, upper) in zip(ranges[::2], ranges[1::2]):
            mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
            if cv2.countNonZero(mask) > 0:
                return color
    return "unknown"

def main():
    cap = cv2.VideoCapture(0)  # Replace with your camera index if different

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            if line == "CHECK_COLOR":
                ret, frame = cap.read()
                if not ret:
                    ser.write(b"ERROR\n")
                    continue

                # Define the region of interest (ROI) where the bead is located
                roi = frame[100:200, 100:200]  # Example coordinates, adjust as needed

                color = detect_color(roi)
                ser.write((color + "\n").encode('utf-8'))

        # (Optional) Display the ROI for debugging
        cv2.imshow("ROI", roi)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
