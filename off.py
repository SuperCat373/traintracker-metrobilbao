from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

# Initialize I2C and PCA9685
i2c_bus = busio.I2C(SCL, SDA)
b0 = PCA9685(i2c_bus, address=0x40)
b1 = PCA9685(i2c_bus, address=0x41)
b2 = PCA9685(i2c_bus, address=0x42)

b0.frequency = 1000
b1.frequency = 1000
b2.frequency = 1000

# Turn off all LEDs
for i in range(16):
    b0.channels[i].duty_cycle = 0
    b1.channels[i].duty_cycle = 0
    b2.channels[i].duty_cycle = 0

b0.deinit()
b1.deinit()
b2.deinit()

print("LEDs turned off.")
