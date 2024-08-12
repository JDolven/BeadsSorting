// Define motor control pins
#define EN_X 48
#define X_DIR 16
#define X_STP 17
#define EN_Y 55
#define Y_DIR 47
#define Y_STP 54

// Define other relevant pins (LED, sensor control)
#define LED 31
#define SENSOR_X 37
#define SENSOR_Y 36

// Variables for stepper motor control and sorting
int delayUs = 250;        // Delay for stepper control (X and Y)
int stepsPerHole = 534;   // Steps to move the disk (X) to the next hole
int stepsPerDegreeArm = 9; // Fine-tuned steps per degree for the arm
int currentArmPosition = 0;  // Current position of the sorting arm (in degrees)
int currentDiskPosition = 0; // Current position of the disk (0 to 5)

// Define positions for each color (in degrees, within 0 to 270 degrees)
int redPosition = 0;
int greenPosition = 15;
int bluePosition = 30;
int yellowPosition = 45;
int orangePosition = 60;
int purplePosition = 75;
int pinkPosition = 90;
int cyanPosition = 105;
int magentaPosition = 120;
int brownPosition = 135;
int blackPosition = 150;
int whitePosition = 165;
int grayPosition = 180;
int goldPosition = 195;
int silverPosition = 210;
int turquoisePosition = 225;
int navyPosition = 240;
int unknownPosition = 255;  // Position for undefined color


// Function to move the sorting arm (Y) to the desired position
void moveArmToPosition(int targetPosition) {
    // Ensure the target position is within the allowed range (0 to 270 degrees)
    if (targetPosition > 270 || targetPosition < 0) {
        Serial.println("Error: Target position is out of bounds.");
        return;
    }

    int movement = targetPosition - currentArmPosition;

    // Calculate the shortest path within the 0 to 270-degree range
    if (movement > 135) {
        // Moving clockwise would exceed 270 degrees, so adjust by moving counterclockwise
        movement -= 270;
    } else if (movement < -135) {
        // Moving counterclockwise would go below 0 degrees, so adjust by moving clockwise
        movement += 270;
    }

    // Ensure that the movement stays within the allowed range
    int newPosition = currentArmPosition + movement;
    if (newPosition < 0) {
        newPosition += 270;
        movement += 270;
    } else if (newPosition > 270) {
        newPosition -= 270;
        movement -= 270;
    }

    // Debug: Print the calculated movement and direction
    Serial.print("Moving arm from ");
    Serial.print(currentArmPosition);
    Serial.print(" degrees to ");
    Serial.print(targetPosition);
    Serial.print(" degrees. Movement: ");
    Serial.print(movement);
    Serial.println(" degrees.");

    if (movement == 0) {
        Serial.println("No movement required, arm already in position.");
        return;
    }

    boolean direction = (movement > 0) ? true : false;

    // Calculate the number of steps required for the arm to move
    long stepsToMove = long(abs(movement)) * long(stepsPerDegreeArm);

    // Debug: Print the direction and steps
    Serial.print("Direction: ");
    Serial.println(direction ? "Clockwise" : "Counterclockwise");
    Serial.print("Steps to move: ");
    Serial.println(stepsToMove);

    // Perform the movement
    step(direction, Y_DIR, Y_STP, stepsToMove);
    currentArmPosition = newPosition;  // Update the current position

    // Debug: Confirm arm movement completion
    Serial.print("Arm moved to ");
    Serial.print(currentArmPosition);
    Serial.println(" degrees.");
}

// Function to control stepper motors
void step(boolean dir, byte dirPin, byte stepperPin, int steps) {
    digitalWrite(dirPin, dir);
    delay(50);
    for (int i = 0; i < steps; i++) {
        digitalWrite(stepperPin, HIGH);
        delayMicroseconds(delayUs);
        digitalWrite(stepperPin, LOW);
        delayMicroseconds(delayUs);
    }
}

// Setup function
void setup() {
    // Initialize serial communication over USB
    Serial.begin(9600);

    // Initialize motor control pins
    pinMode(EN_X, OUTPUT);
    pinMode(X_DIR, OUTPUT);
    pinMode(X_STP, OUTPUT);
    pinMode(EN_Y, OUTPUT);
    pinMode(Y_DIR, OUTPUT);
    pinMode(Y_STP, OUTPUT);

    // Initialize other pins
    pinMode(LED, OUTPUT);
    pinMode(SENSOR_X, INPUT);
    pinMode(SENSOR_Y, INPUT);

    // Initial alignment check
    if (!checkAlignment()) {
        Serial.println("Initial alignment failed, please adjust the rotor.");
    } else {
        Serial.println("Rotor aligned successfully at startup.");
    }
}

// Function to request color detection from Raspberry Pi
String requestColor() {
    Serial.println("CHECK_COLOR");
    while (!Serial.available()) {
        // Wait for response
    }
    String color = Serial.readStringUntil('\n');
    return color;
}

// Function to check rotor alignment with Raspberry Pi
bool checkAlignment() {
    // Disable the X stepper motor during alignment
    digitalWrite(EN_X, HIGH);  // Disable the X stepper motor

    Serial.println("CHECK_ALIGNMENT");
    while (!Serial.available()) {
        // Wait for response
    }
    String response = Serial.readStringUntil('\n');

    // Enable the X stepper motor after the alignment check, regardless of success
    digitalWrite(EN_X, LOW);  // Enable the X stepper motor

    return (response == "ROTOR_ALIGNED");
}

// Function to move the disk (X) to the next hole, including a pause at the drop-off position
void moveDiskToNextHole() {
    int stepsToDropOff = stepsPerHole / 2;  // Half the steps to the next hole
    step(false, X_DIR, X_STP, stepsToDropOff);  // Rotate to the drop-off position

    delay(1000);  // Pause to let the bead fall out (adjust the delay as needed)

    step(false, X_DIR, X_STP, stepsToDropOff);  // Rotate the remaining steps to the next hole
    currentDiskPosition = (currentDiskPosition + 1) % 6;  // Update the position (0 to 5)
}

// Main loop
void loop() {
    // Move disk to the next hole
    moveDiskToNextHole();

    // Wait for the bead to be in front of the camera
    delay(500);  // Adjust delay as needed to allow for detection

    // Request color from Raspberry Pi
    String detectedColor = requestColor();
    Serial.println("Detected Color: " + detectedColor);

    // Determine the target position for the sorting arm based on the detected color
    int targetPosition = currentArmPosition;
    if (detectedColor == "red") {
        targetPosition = redPosition;
    } else if (detectedColor == "green") {
        targetPosition = greenPosition;
    } else if (detectedColor == "blue") {
        targetPosition = bluePosition;
    } else if (detectedColor == "yellow") {
        targetPosition = yellowPosition;
    } else if (detectedColor == "orange") {
        targetPosition = orangePosition;
    } else if (detectedColor == "purple") {
        targetPosition = purplePosition;
    } else if (detectedColor == "pink") {
        targetPosition = pinkPosition;
    } else if (detectedColor == "cyan") {
        targetPosition = cyanPosition;
    } else if (detectedColor == "magenta") {
        targetPosition = magentaPosition;
    } else if (detectedColor == "brown") {
        targetPosition = brownPosition;
    } else if (detectedColor == "black") {
        targetPosition = blackPosition;
    } else if (detectedColor == "white") {
        targetPosition = whitePosition;
    } else if (detectedColor == "gray") {
        targetPosition = grayPosition;
    } else if (detectedColor == "gold") {
        targetPosition = goldPosition;
    } else if (detectedColor == "silver") {
        targetPosition = silverPosition;
    } else if (detectedColor == "turquoise") {
        targetPosition = turquoisePosition;
    } else if (detectedColor == "navy") {
        targetPosition = navyPosition;
    } else {
        // Unknown color detected, move to the predefined unknown position
        Serial.println("Unknown color detected, moving to unknown position...");
        targetPosition = unknownPosition;
    }

    // Move the arm to the target position
    moveArmToPosition(targetPosition);

    // Drop off the bead as the disk continues to rotate
    delay(1000);  // Adjust delay as needed for bead drop-off
}
