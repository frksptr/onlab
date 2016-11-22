from pymodbus.client.sync import ModbusTcpClient
from helper import Edge, Filter
import sys
import numpy as np
import RPi.GPIO as GPIO


class Msg:
    msg = ""
    cnt = 0
    cursorup = '\033[F'
    erase = '\033[K'
    en = 1;
    def printMsg(self, msg):
        if (self.en == 0):
            return
        print(msg)
        #if (self.msg is msg):
         #   if (self.cnt > 1) :
          #      print(self.cursorup+self.erase)
           # self.cnt += 1
            #print(msg + " ({})".format(self.cnt))
        #else:
         #  self.cnt = 0
           #self.msg = msg
           #print(msg)


#y 30 110
#x 360 440
#z 25

def getSigned16bit(a):
    if (a >> 15) & 1:
        return a - (1 << 16)
    return a

GPIO.setmode (GPIO.BCM)
GPIO.setup(4, GPIO.IN)


dataReadyReg = 500;
dataXReg = 1000;
dataYReg = 1002;
newDataReadyReg = 1006;
dataRead = 0;
fileName = "test1610.txt";

pointArray = np.array([]);

client = ModbusTcpClient('192.168.0.104',502)
conn = client.connect()

SignalFilter = Filter(16)
SignalEdge = Edge()
ReadyEdge = Edge()
msg = Msg();


edgeDetected = 0
dataReadyEdgeDetected = 0

while 1:

    input_v = GPIO.input(4)

    signal = SignalFilter.step(input_v)
    
    signalEdge = SignalEdge.chk(signal)
    signalType = signalEdge['type']
    signalEdge = signalEdge['value']
        
    dataReady = client.read_holding_registers(newDataReadyReg,1)
    
    if (dataReady == None):
        msg.printMsg("dataready none")
        continue
    
    dataReady = dataReady.registers[0]
       
    if (signalEdge and dataReady == 0):
        edgeDetected = 1
        client.write_register(500, 1)
        msg.printMsg("\n Edge detected, setting Reg500 to 1")
        
    if (edgeDetected):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        dataReady = dataReady.registers[0]
        msg.printMsg("\n Checking if data is ready: {}".format(dataReady))

        readyEdge = ReadyEdge.chk(dataReady)['value']
        if (readyEdge):
            dataReadyEdgeDetected = 1;
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
        
        
        if(dataReadyEdgeDetected and dataReady):
            msg.printMsg("\n Reading out data from registers...")
            xy = client.read_holding_registers(dataXReg,4);
            x = getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])
            
            with open(fileName, "a") as myfile:
                myfile.write("\n {}, {}, ".format(x,y) + signalType)
                
            dataRead = 1;
            pointArray = np.append(pointArray, [x,y]);
            dataReadyEdgeDetected = 0;
            edgeDetected = 0;
            msg.printMsg("\n Data read, setting Reg500 to 0")
            client.write_register(500, 0)

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))

client.close()

