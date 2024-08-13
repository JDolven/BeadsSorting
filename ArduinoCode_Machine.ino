// Define motor control pins
#define EN_X 48
#define X_DIR 16
#define X_STP 17
#define EN_Y 55
#define Y_DIR 47
#define Y_STP 54

// Variables for stepper motor control and sorting
int delayUs = 250;        // Delay for stepper control (X and Y)
int stepsPerHole = 534;   // Steps to move the disk (X) to the next hole
int stepsPerDegreeArm = 9; // Fine-tuned steps per degree for the arm
int currentArmPosition = 0;  // Current position of the sorting arm (in degrees)
int currentDiskPosition = 0; // Current position of the disk (0 to 5)
int diskRotations = 0;      // Number of rotations for the disk

// Define positions for each box number (in degrees, within 0 to 270 degrees)
int boxPositions[18] = {
    0, 15, 30, 45, 60, 75, 90, 105, 120, 
    135, 150, 165, 180, 195, 210, 225, 240, 255
};

// Function to move the sorting arm (Y) to the desired position
void moveArmToPosition(int targetPosition) {
    // Ensure the target position is within the allowed range (0 to 270 degrees)
    if (targetPosition > 270 || targetPosition < 0) {
        Serial.println("Error: Target position is out of bounds.");
        return;
    }

    int movement = targetPosition - currentArmPosition;

    if (movement == 0) {
        Serial.println("No movement required, arm already in position.");
        return;
    }

    boolean direction = (movement > 0) ? true : false;

    // Calculate the number of steps required for the arm to move
    long stepsToMove = long(abs(movement)) * long(stepsPerDegreeArm);

    // Perform the movement
    step(direction, Y_DIR, Y_STP, stepsToMove);
    currentArmPosition = targetPosition;  // Update the current position

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

    // Enable stepper motors at startup
    enableSteppers();
}

// Function to process incoming serial commands
void processSerialCommand(String command) {
    command.trim();  // Remove any leading/trailing whitespace

    if (command.equalsIgnoreCase("DISABLE")) {
        disableSteppers();
    } else if (command.equalsIgnoreCase("ENABLE")) {
        enableSteppers();
    } else if (command.startsWith("DISK")) {
        int rotations = command.substring(4).toInt();
        if (rotations > 0) {
            diskRotations = rotations;
            Serial.print("Starting disk rotation with ");
            Serial.print(diskRotations);
            Serial.println(" moves.");
            performDiskRotations(diskRotations);
        } else {
            Serial.println("Invalid number of rotations for disk.");
        }
    } else if (command.startsWith("ARM")) {
        int boxNumber = command.substring(3).toInt();
        if (boxNumber >= 1 && boxNumber <= 18) {
            // Get the target position based on the box number
            int targetPosition = boxPositions[boxNumber - 1];

            // Move the arm to the target position
            moveArmToPosition(targetPosition);
        } else {
            Serial.println("Invalid command or box number.");
        }
    } else if (command.startsWith("STEP_DISK")) {
        int steps = command.substring(9).toInt();
        if (steps != 0) {
            boolean direction = (steps < 0);
            step(direction, X_DIR, X_STP, abs(steps));
            Serial.print("X stepper moved ");
            Serial.print(abs(steps));
            Serial.println(" steps.");
        } else {
            Serial.println("Invalid step count for X stepper.");
        }
    } else if (command.startsWith("STEP_ARM")) {
        int steps = command.substring(8).toInt();
        if (steps != 0) {
            boolean direction = (steps > 0);
            step(direction, Y_DIR, Y_STP, abs(steps));
            Serial.print("Y stepper moved ");
            Serial.print(abs(steps));
            Serial.println(" steps.");
        } else {
            Serial.println("Invalid step count for Y stepper.");
        }
    } else {
        int boxNumber = command.toInt();
        if (boxNumber >= 1 && boxNumber <= 18) {
            // Get the target position based on the box number
            int targetPosition = boxPositions[boxNumber - 1];

            // Move the arm to the target position
            moveArmToPosition(targetPosition);
            // After moving the arm, rotate the disk with a 1-second delay
            moveDiskToNextHole(1000);
        } else {
            Serial.println("Invalid command or box number.");
        }
    }
}

// Function to disable both X and Y stepper motors
void disableSteppers() {
    digitalWrite(EN_X, HIGH);  // Disable the X stepper motor
    digitalWrite(EN_Y, HIGH);  // Disable the Y stepper motor
    Serial.println("Steppers disabled.");
}

// Function to enable both X and Y stepper motors
void enableSteppers() {
    digitalWrite(EN_X, LOW);  // Enable the X stepper motor
    digitalWrite(EN_Y, LOW);  // Enable the Y stepper motor
    Serial.println("Steppers enabled.");
}

// Function to perform a series of disk rotations with zero delay
void performDiskRotations(int rotations) {
    for (int i = 0; i < rotations; i++) {
        moveDiskToNextHole(0);  // Perform rotation with zero delay
    }
    Serial.println("Disk rotations completed.");
}

// Function to move the disk (X) to the next hole, with a specified delay
void moveDiskToNextHole(int delayTime) {
    int stepsToDropOff = stepsPerHole / 2;  // Half the steps to the next hole
    step(false, X_DIR, X_STP, stepsToDropOff);  // Rotate to the drop-off position

    delay(delayTime);  // Pause to let the bead fall out or perform action

    step(false, X_DIR, X_STP, stepsToDropOff);  // Rotate the remaining steps to the next hole
    currentDiskPosition = (currentDiskPosition + 1) % 6;  // Update the position (0 to 5)
}

// Main loop
void loop() {
    // Check if there is any serial input
    if (Serial.available() > 0) {
        String incomingCommand = Serial.readStringUntil('\n');
        processSerialCommand(incomingCommand);
    }

    // Drop off the bead as the disk continues to rotate
    delay(1000);  // Adjust delay as needed for bead drop-off
}
