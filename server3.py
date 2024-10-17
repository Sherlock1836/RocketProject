import socket

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)


try:
    cl, addr = s.accept()
    print("Enter 'start' to start sensors")
    cl.send(input().encode("utf-8"))
    print("sent command")
    cl.close()
except OSError as e:
    cl.close()
    print('connection closed')

while True:      
    try:
        cl, addr = s.accept()
        data = cl.recv(1024)
        print(data.decode())
        cl.close()
    except OSError as e:
        cl.close()
    except KeyboardInterrupt:
        cl.close()
