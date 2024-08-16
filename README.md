# Bead Sorting Machine

Welcome to the Bead Sorting Machine project! This repository contains the code and resources for building and programming a bead sorting machine designed to automatically identify and sort beads by color.

The bead sorting machine is built using 3D-printed mechanical parts, an Arduino-based controller for motor control, and a PC with a webcam for color detection. The system is designed to sort beads by color, with stepper motors handling the mechanical movement, and image processing algorithms determining the bead color from the webcam feed.

## Hardware Components

### 3D-Printed Parts
The mechanical parts of the bead sorting machine are based on the design available on [Thingiverse](https://www.thingiverse.com/thing:5228416). These parts are used as-is to build the structure of the sorting machine.

### Arduino-Based Controller with Stepper Drives
An Arduino-based controller is used to control the stepper motors responsible for the movement of the beads through the sorting mechanism. The controller runs on Arduino code that manages the timing, direction, and speed of the motors, ensuring accurate positioning during the sorting process.

*Note:* While the provided Arduino code is tailored for a specific controller, it is modular and can be easily adapted to work with other Arduino-compatible boards and stepper drives. If you choose to use a different board, you may need to adjust the pinouts and stepper motor resolution accordingly.

### PC & Webcam
The PC is responsible for higher-level processing, including capturing images from the webcam and analyzing them to determine the color of each bead. The Python scripts on the PC handle the image processing and decision-making, communicating with the Arduino-based controller to direct the sorting process based on the detected color.

## Software Components

### Arduino Code for Stepper Control
The Arduino code in this repository is responsible for controlling the stepper motors. It manages the motor movements, ensuring the beads are positioned correctly for the webcam to capture their images. The code is modular, allowing for easy modifications if you wish to use a different controller or add more features. If using a different board, remember to update the pin assignments and stepper motor resolution settings as needed.

### Python Code for Image Processing
The Python scripts run on a computer, utilizing libraries for image processing to detect bead colors from the webcam feed. Once the color is identified, the Python code sends commands to the Arduino-based controller to direct the bead to the appropriate bin.
