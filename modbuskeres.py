from pymodbus.client.sync import ModbusTcpClient
from helper import Edge, Filter
import sys
import numpy as np
import RPi.GPIO as GPIO
from statemachine import StateMapElement, StateMachine
from ujkeres import ujkeres

class Msg:
    msg = ""
    cnt = 0
    cursorup = '\033[F'
    erase = '\033[K'
    en = 0;
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

client = ModbusTcpClient('192.168.0.104',502)
conn = client.connect()

SignalFilter = Filter(16)
SignalEdge = Edge()
ReadyEdge = Edge()
msg = Msg();


edgeDetected = 0
dataReadyEdgeDetected = 0

stateMap = [
    StateMapElement("SignalRise","SignalWait","GetPosition"),
    StateMapElement("RobotPositionReady","GetPosition","CheckPositionList"),
    StateMapElement("GetMoreInitialPos","CheckPositionList","ReturnMovement"),
    StateMapElement("GetNextPos","CheckPositionList","CalculateNewPosition"),
    StateMapElement("RetMov","ReturnMovement","SignalWait"),
    StateMapElement("NewPositionSet","CalculateNewPosition","WaitScanReady"),
    StateMapElement("ScanReady","WaitScanReady","SignalWait"),
]

stateMachine = StateMachine(stateMap)

pointArray = []

client.write_register(500, 0)

while 1:
    signalType = ""

    cs = stateMachine.currentState

    # Waits for RFID signal edge
    if (cs == "SignalWait"):
        input_v = GPIO.input(4)    

        signal = SignalFilter.step(input_v)
        
        signalEdge = SignalEdge.chk(signal)
        signalType = signalEdge['type']

        # Notify robot of RFID signal change
        if (signalEdge['value'] == 1):
            msg.printMsg("\n Edge detected, setting Reg500 to 1")
            client.write_register(500, 1)
            stateMachine.event("SignalRise")
            continue

    # Gets robot's current position data    
    elif (cs == "GetPosition"):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        msg.printMsg("\n Checking if data is ready: {}".format(dataReady))
       
        if (dataReady == None):
            msg.printMsg("dataready none")
            continue
        dataReady = dataReady.registers[0]

        readyEdge = ReadyEdge.chk(dataReady)['value']

        if (readyEdge):
            xy = client.read_holding_registers(dataXReg,4)
            x =  getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])
            pointArray.append([x,y])
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
            stateMachine.event("RobotPositionReady")
            continue

    # Check if we already have two position data and can calculate next one
    elif (cs == "CheckPositionList"):
        print("{}, length: {} ".format(pointArray,len(pointArray)))
        if (len(pointArray) < 2):
            stateMachine.event("GetMoreInitialPos")
        else:
            stateMachine.event("GetNextPos")

    # Need to find more points, return robot movement as it were
    elif (cs == "ReturnMovement"):
        client.write_register(500,2)
        stateMachine.event("RetMov")
        

    # Calculates new position data and sends it to robot
    elif (cs == "CalculateNewPosition"):
        newPointData = ujkeres(pointArray[0],pointArray[1],60)
        newStart = newPointData["kezdo"]
        newEnd = newPointData["veg"]

        client.write_register(502, 10)
        client.write_register(504, 0)

        client.write_register(506, 0)
        client.write_register(508, 10)

        client.write_register(500, 0)

        stateMachine.event("NewPositionSet")

    elif (cs == "WaitScanReady"):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        dataReady = dataReady.registers[0]
        if (dataReady == 5):
            stateMachine("ScanReady")

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))



client.close()
