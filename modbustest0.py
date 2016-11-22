from pymodbus.client.sync import ModbusTcpClient
import sys

import RPi.GPIO as GPIO

GPIO.setmode (GPIO.BCM)

GPIO.setup(4, GPIO.IN)




try:
    client = ModbusTcpClient('192.168.0.104',502)
    conn = client.connect()
    print(conn)
    while 1==1: 
        input_v = GPIO.input(4)
        
        
    print(sys.argv[1])
    client.write_register(500, int(sys.argv[1]))
    client.close()
except:
    print(sys.exc_info()[0])
    raise
