# Bead Sorting Machine

Welcome to the Bead Sorting Machine project! This repository contains the code and resources for building and programming a bead sorting machine, designed to automatically identify and sort beads by color.

The bead sorting machine is built using 3D-printed mechanical parts, an Arduino-compatible Rumba board for motor control, and a Raspberry Pi 3 with a webcam for color detection. The system is designed to sort beads by color, with two stepper motors handling the mechanical movement, and image processing algorithms determining the bead color from the webcam feed.

# Hardware Components
## 3D-Printed Parts
The mechanical parts of the bead sorting machine are based on the design available on [Thingiverse](https://www.thingiverse.com/thing:5228416). These parts have not been modified and are used as-is to build the structure of the sorting machine.

## RUMBA Board (Arduino-based)
The Rumba board is used to control the two stepper motors responsible for the movement of the beads through the sorting mechanism. The board runs on Arduino code that manages the timing, direction, and speed of the motors, ensuring accurate positioning during the sorting process.

Note: While the provided Arduino code is tailored for the Rumba board, it is modular and can be easily adapted to work with other Arduino-compatible boards. If you choose to use a different board, you will need to adjust the pinouts and stepper motor resolution accordingly.

## Raspberry Pi 3 & Webcam
The Raspberry Pi 3 is responsible for the higher-level processing, including capturing images from the webcam and analyzing them to determine the color of each bead. The Python scripts on the RPi handle the image processing and decision-making, communicating with the Rumba board (or another compatible board) to direct the sorting process based on the detected color.

# Software Components
## Arduino Code for RUMBA Board
The Arduino code in this repository is responsible for controlling the stepper motors. It manages the motor movements, ensuring the beads are positioned correctly for the webcam to capture their images. The code is modular, allowing for easy modifications if you wish to use a different board or add more features. If using a different board, remember to update the pin assignments and stepper motor resolution settings as needed.

## Python Code for Raspberry Pi
The Python scripts run on the Raspberry Pi, utilizing libraries for image processing to detect bead colors from the webcam feed. Once the color is identified, the Python code sends commands to the Rumba board (or other compatible boards) to direct the bead to the appropriate bin.

# Getting Started
Please note: Building this project requires some experience with 3D printing, electronics, and programming. While the repository provides the necessary code and resources, detailed step-by-step instructions are not included. This project is intended for builders who are comfortable with customizing and troubleshooting hardware and software.

    3D Print the Mechanical Parts: Download and print the necessary parts from Thingiverse to build the sorting machine's structure.
    Set Up the Hardware: Assemble the machine with the printed parts, connect the stepper motors to the Rumba board, and attach the webcam to the Raspberry Pi.
    Upload the Arduino Code: Flash the Arduino code onto the Rumba board (or your chosen board) to control the stepper motors. Be sure to change the pinouts and stepper motor resolution settings in the code if using a different board.
    Run the Python Scripts: Set up your Raspberry Pi with the necessary Python libraries and run the image processing scripts to start sorting beads by color.
