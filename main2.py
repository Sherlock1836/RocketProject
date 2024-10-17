from machine import Pin, I2C, reset
from time import sleep, time_ns
import network
import socket
import BME280
import H3LIS331DL

# Initialize I2C communication for bme
bme_i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=10000)
sleep(.2)
# Initialize BME280 sensor
bme = BME280.BME280(i2c=bme_i2c)
# Initialize I2C communication for H3LIS331DL
accel_i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=500000)
sleep(1)
accel = H3LIS331DL.H3LIS331DL(i2c=accel_i2c)

# Set BDU on for accelerometer (might not be necessary)
accel.set_bdu_on(True)

# Calibrate accelerometer
# accel.manually_calibrate() can call this to get offsets...I already have 
accel.set_offsets((-0.1214193, -0.234375, -1.440755))

# Open the file to write data to
try: 
    file = open("data.csv", "w")  # open the file for writing if it exists
except: 
    file = open("data.csv", "x")  # if it doesn't exist, create it and open it for writing
    
# Write titles for each column
file.write("Time, TempC, TempF, Humidity, Pressure, AccelX, AccelY, AccelZ\n")

try:
    while True:
        # Read sensor data from bme
        tempC = bme.temperature
        hum = bme.humidity
        pres = bme.pressure
        
        # Convert temperature to fahrenheit
        tempF = (bme.read_temperature()/100) * (9/5) + 32
        tempF = str(round(tempF, 2)) + 'F'
        
        # Read sensor data from accelerometer (x, y, z)
        accelData = accel.read_accel_data()

        # Prepare data
        data = [
            time_ns(),
            tempC,
            tempF,
            hum,
            pres,
            accelData[0],
            accelData[1],
            accelData[2]
        ]

        # Convert all elements to strings and join them with ', ' as the separator
        line = ', '.join(map(str, data)) + '\n'
        
        # Write to file
        file.write(line)
        file.flush()
except KeyboardInterrupt:
    print("Stopped")
    file.close()