import socket
from time import sleep 
import network
import machine

ssid = "Patty's Galaxy A32 "
password = "is45aia22h"

ip = '192.168.117.178'
port = 80
print("netTest")

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    print("connected")
    
        
try:
    connect()
except KeyboardInterrupt:
    machine.reset()
    
ai = socket.getaddrinfo(ip, port)
addr = ai[0][-1]
while True:
    i = 0
    try:
        s = socket.socket()
        s.connect(addr)
        print('socket connected')
        s.send(b"requesting data...")
        print("sent request")
        reply = str(s.recv(512))
        print(reply, i)
        s.close()
        sleep(0.2)
    except OSError as e:
        print(e)
        s.close()
    i = i+1