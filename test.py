import time
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

# Initialize I2C and PCA9685 boards
i2c = busio.I2C(SCL, SDA)
pca1 = PCA9685(i2c, address=0x40)
pca2 = PCA9685(i2c, address=0x41)
pca3 = PCA9685(i2c, address=0x42)

pca1.frequency = 1000
pca2.frequency = 1000
pca3.frequency = 1000

# Function to turn all ports on or off
def control_all_ports(pwm_value, delay=1):
    """
    Set all channels to a specific duty cycle on all boards.

    :param pwm_value: Duty cycle (0 to 65535)
    :param delay: Time in seconds to keep the channels on/off
    """
    # Loop through all 16 channels and set PWM
    for i in range(16):
        pca1.channels[i].duty_cycle = pwm_value
        pca2.channels[i].duty_cycle = pwm_value
        pca3.channels[i].duty_cycle = pwm_value

    if pwm_value > 0:
        print("All ports ON")
    else:
        print("All ports OFF")

    time.sleep(delay)

# Function to turn everything off safely
def shutdown_all_ports():
    print("Shutting down...")
    control_all_ports(0)  # Set all channels to 0 (off)
    pca1.deinit()
    pca2.deinit()
    pca3.deinit()
    print("All ports OFF and PCA9685 deinitialized.")

try:
    while True:
        control_all_ports(65535, delay=1)  # Full brightness/power
        control_all_ports(0, delay=1)      # Turn everything off

except KeyboardInterrupt:
    # Graceful exit and turn everything off
    shutdown_all_ports()