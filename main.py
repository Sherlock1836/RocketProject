from machine import Pin, I2C, reset
from time import sleep, time_ns
import network
import socket
import BME280
import H3LIS331DL

# network connection data
ssid = "Sherlock Moto"
password = "Holmes1836"
ip = '192.168.216.178' # ip of device serving socket connection
port = 80
wlan = network.WLAN(network.STA_IF)

# used to connect to wifi 
def connect():
    #Connect to WLAN
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    print("connected!")

# connect to wifi
print("connecting to wifi...")
try:
    connect()
except KeyboardInterrupt:
    reset()

# set up address to connect at
addressInfo = socket.getaddrinfo(ip, port)
address = addressInfo[0][-1]

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

# connect socket and wait for start command
while True:
    try: 
        s = socket.socket()
        s.connect(address)
        print("listening for start...")
        resp = s.recv(512)
        if(resp.decode() == 'start'):
            s.close()
            break
        s.close()
        sleep(.2)
    except OSError as e:
        print(e)
        s.close()

print("Started!")

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
        if wlan.isconnected():
            try: 
                s = socket.socket()
                s.settimeout(0.2)
                s.connect(address)
                s.send(line.encode("utf-8"))
                s.close()
            except OSError as e:
                print(e)
                s.close()
except KeyboardInterrupt:
    print("Stopped")
    file.close()
    s.close()