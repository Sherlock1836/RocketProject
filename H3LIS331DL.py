"""
A lightweight MicroPython implementation for interfacing with the H3LIS331DL using I2C. 
Author: Isaac Reynolds - https://github.com/Sherlock1836 (this driver isn't posted yet)
Version: 1.0
"""
import machine
from time import sleep

class H3LIS331DL:
    def __init__(self, i2c:machine.I2C, address:int = 0x19):
        self.address = address
        self.i2c = i2c
        self.xError: float = 0
        self.yError: float = 0
        self.zError: float = 0
        self.bdu_on: bool = False
        self.current_range: int
        self.lsb_value: float
        self.turn_on()
        self._set_lsb_val()
        
    def turn_on(self):
        """Turns on the sensor with power mode normal, freq 50HZ and all 3 axis enabled""" 
        self.i2c.writeto_mem(self.address, 0x20, bytes([0x27]))
        
    def read_range(self) -> int:
        """Reads the current range and returns it as int (should be 100 200 or 400)"""
        hexRange = self.i2c.readfrom_mem(self.address, 0x23, 1)[0]
        if hexRange == 0x00 or hexRange == 0x80:
            intRange = 100
        elif hexRange == 0x10 or hexRange == 0x90:
            intRange = 200
        elif hexRange == 0x18 or hexRange == 0xB0:
            intRange = 400
        else: 
            raise Exception("Unknown accel range read '", str(hexRange), "'")
        self.current_range = intRange
        return intRange
        
    def set_range(self, intRange: int):
        """Sets the range to intInput...valid inputs are 100 200 or 400. 100 is default"""
        if intRange == 100:
            if self.bdu_on:
                hexVal = 0x80
            else:
                hexVal = 0x00
        elif intRange == 200:
            if self.bdu_on:
                hexVal = 0x90
            else:   
                hexVal = 0x10
        elif intRange == 400:
            if self.bdu_on:
                hexVal = 0xB0
            else:
                hexVal = 0x18
        else:
            raise Exception("Invalid input...must be 100 200 or 400")
        self.current_range = intRange
        self.i2c.writeto_mem(self.address, 0x23, bytes([hexVal]))
        self._set_lsb_val()
        
    def read_accel_data(self) -> tuple[float, float, float]:
        """Reads current acceleration value for all 3 axis (returns (x, y, z))"""
        lowX = self.i2c.readfrom_mem(self.address, 0x28, 1)
        highX = self.i2c.readfrom_mem(self.address, 0x29, 1)
        x: float = self._translate_pair(high=int.from_bytes(highX, 'big'), low=int.from_bytes(lowX, 'big')) * self.lsb_value + self.xError
        
        lowY = self.i2c.readfrom_mem(self.address, 0x2A, 1)
        highY = self.i2c.readfrom_mem(self.address, 0x2B, 1)
        y: float = self._translate_pair(high=int.from_bytes(highY, 'big'), low=int.from_bytes(lowY, 'big')) * self.lsb_value + self.yError
        
        lowZ = self.i2c.readfrom_mem(self.address, 0x2C, 1)
        highZ= self.i2c.readfrom_mem(self.address, 0x2D, 1)
        z: float = self._translate_pair(high=int.from_bytes(highZ, 'big'), low=int.from_bytes(lowZ, 'big')) * self.lsb_value + self.zError
        
        return (x, y, z)
    
    def _translate_pair(self, high:int, low:int) -> int:
        """Converts a byte pair to a usable value. Modified from https://github.com/m-rtijn/mpu6050/blob/0626053a5e1182f4951b78b8326691a9223a5f7d/mpu6050/mpu6050.py#L76C39-L76C39."""
        value = (high << 8) + low
        value >>= 4 #need to right shift 4 bits to get 12 bits (which is what the h3lis outputs)
        #output is in 2s complement form, so we convert it here
        if value >= 0x800: #0x800 is the MSBs value for 12 bits
            value = -((4095 - value) + 1) #4095 is the greatest possible value for 12 bits (all 1s)
        return value 
    
    def _set_lsb_val(self):
        """sets the lsb value for use in read_accel_range (used to get readable data)"""
        #4096 is twice the decimal value of 1000 0000 0000 (12 bits)
        self.lsb_value = 2 * self.read_range() * float(1) / 4096
    
    def hp_filter_reset(self):
        """Instantaneously resets the content of the internal high pass filter"""
        self.i2c.readfrom_mem(self.address, 0x25, 1)
    
    def set_hp_filter(self, level:int):
        """Set the internal high-pass filter: 0 is off, 4 is max filter (hp filter is off by default)"""
        if level == 0:
            hexVal = 0x00
        elif level == 1:
            hexVal = 0x10
        elif level == 2:
            hexVal = 0x11
        elif level == 3:
            hexVal = 0x12
        elif level == 4:
            hexVal = 0x13
        
        if level > 4 or level < 0:
            raise Exception("Invalid level...Must be 0-4")
        
        self.i2c.writeto_mem(self.address, 0x21, bytes([hexVal]))
    
    def manually_calibrate(self) -> tuple[float, float, float]:
        """This function will calculate an offset to apply to x y and z axis, and will apply it.
            They will NOT save to the sensor! You can either call this function everytime you use 
            the sensor, or call it once through the repl, note the results, and apply it manually
            to your program to save time. A set_offsets function is available to make this easy
            When calibrating:
            Set sensor on a flat surface facing up, and leave it still for 15 seconds (duration of 
            the function call). LED will come on for duration of calibration if using piPico
            """
        machine.Pin("LED", machine.Pin.OUT).on()
        xSum: float = 0
        ySum: float = 0
        zSum: float = 0
        sampleSize = 150
        for i in range(sampleSize):
            xSum += 0 - self.read_accel_data()[0]
            ySum += 0 - self.read_accel_data()[1]
            zSum += 1 - self.read_accel_data()[2]
            sleep(0.1)
        self.xError = xSum / sampleSize
        self.yError = ySum / sampleSize
        self.zError = zSum / sampleSize
        machine.Pin("LED", machine.Pin.OUT).off()
        return (self.xError, self.yError, self.zError)
    
    def set_bdu_on(self, isOn: bool):
        """When the BDU is activated, the content of the output registers
            is not updated until both MSB and LSB are read, which avoids
            reading values related to different sample times
            Idk if this is important to use, but here it is."""
        if(isOn != self.bdu_on):
            self.bdu_on = isOn
            self.set_range(self.current_range)
            
    def set_offsets(self, offsetTuple=(0, 0, 0)):
        """Use this to set the offsets (for error correction) for each axis.
            Tuple should be in form (x, y, z) To get offsets, use manually_calibrate()"""
        self.xError = offsetTuple[0]
        self.yError = offsetTuple[1]
        self.zError = offsetTuple[2]
        