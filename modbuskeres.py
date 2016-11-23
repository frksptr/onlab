from pymodbus.client.sync import ModbusTcpClient
from helper import Edge, Filter
import sys
import numpy as np
import RPi.GPIO as GPIO
from statemachine import StateMapElement, StateMachine
from datetime import datetime
from ujkeres import ujkeres
from korkeres import findCircle
import time

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

#406-33

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
    StateMapElement("FalsePosition","GetPosition","ReturnMovement"),
    StateMapElement("GetMoreInitialPos","CheckPositionList","ReturnMovement"),
    StateMapElement("GetNextPos","CheckPositionList","CalculateNewPosition"),
    StateMapElement("RetMov","ReturnMovement","SignalWait"),
    StateMapElement("NewPositionSet","CalculateNewPosition","WaitScanReady"),
    StateMapElement("ScanReady","WaitScanReady","SignalWait"),
    StateMapElement("ReturnScanning","CheckPositionList","ReturnMovement"),
    StateMapElement("IterationOver","CheckPositionList","CalculateCenter"),
    StateMapElement("Finished","CalculateCenter","Stop"),
]

stateMachine = StateMachine(stateMap)

pointArray = []
currPos = []

client.write_register(500, 0)
client.write_register(510, 0)


def setNeg(n):
    if (n < 0):
        return n+pow(2,16);
    else:
        return n;

t = datetime.now().time().strftime("%H%M%S")
f = "./meres/30keres"+t+".txt"

def log(s):
    with open(f, "a") as myfile:
        myfile.write(s)
    return

scanPoints = []
scanning = 0
pointsx = []
pointsy = []
iterationCounter = 0
maxIterations = 4

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
            time.sleep(0.5)
            xy = client.read_holding_registers(dataXReg,4)
            x =  getSigned16bit(xy.registers[0])
            y = getSigned16bit(xy.registers[2])
            if (len(currPos)>0):
                d = np.linalg.norm(np.array([x,y])-np.array(currPos))
                if (d < 10):
                    stateMachine.event("FalsePosition")
                    continue

            currPos = [x,y]
            pointsx.append(float(x))
            pointsy.append(float(y))
            log("\n {},{}".format(x,y))
            pointArray.append(currPos)
            msg.printMsg("\n Data ready signal changed to {}".format(dataReady))
            stateMachine.event("RobotPositionReady")
            continue

    # Check if we already have two position data and can calculate next one
    elif (cs == "CheckPositionList"):
        print("{}, length: {} ".format(pointArray,len(pointArray)))
        if (scanning == 1):
            scanPoints.append(currPos)
            if (len(scanPoints) < 2):
                stateMachine.event("ReturnScanning")
            else:
                scanPoints = []
                if (iterationCounter == maxIterations):
                    print("getting center")
                    stateMachine.event("IterationOver")
                    continue
                stateMachine.event("GetNextPos")
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
        newPointData = ujkeres(pointsx,pointsy,30)
        iterationCounter += 1
        newStart = newPointData["kezdo"]
        newEnd = newPointData["veg"]

        log("\n {},{}, start".format(newStart.astype(int)[0],newStart.astype(int)[1]))
        log("\n {},{}, end".format(newEnd.astype(int)[0],newEnd.astype(int)[1]))

        newSd = newStart - currPos
        newEd = newEnd - currPos

        nxd = newSd.astype(int)[0]
        nyd = newSd.astype(int)[1]

        nexd = newEd.astype(int)[0]
        neyd = newEd.astype(int)[1]
        

        print("Scan positions: {} -> {} ".format(newStart,newEnd))
        #print("nxd nyd {} {}".format(nxd,nyd))
        #print("nexd neyd {} {}".format(nexd,neyd))

        nxd = setNeg(nxd)
        nyd = setNeg(nyd)

        nexd = setNeg(nexd)
        neyd = setNeg(neyd)
        
        client.write_register(502, nxd)
        client.write_register(504, nyd)

        client.write_register(506, nexd)
        client.write_register(508, neyd)

        client.write_register(500, 0)
        scanning = 1
        stateMachine.event("NewPositionSet")

    #Calculates and moves to center
    elif (cs == "CalculateCenter"):
        c = findCircle(pointsx,pointsy)
        print("findcircle: {}, current pos: {}".format(c,currPos))
        c = np.array(c)       
        c = c - currPos

        cx = setNeg(c.astype(int)[0])
        cy = setNeg(c.astype(int)[1])

        client.write_register(512, cx)
        client.write_register(514, cy)
        time.sleep(0.5)
        client.write_register(500, 5)
        client.write_register(510, 1)
        stateMachine.event("Finished")

    elif (cs == "Stop"):
        var = raw_input("finished?")
        log("finished")
        

    elif (cs == "WaitScanReady"):
        dataReady = client.read_holding_registers(newDataReadyReg,1)
        dataReady = dataReady.registers[0]
        if (dataReady == 5):
            stateMachine.event("ScanReady")

    #msg.printMsg("input: {} | filtered: {} | edge: {} ".format(input_v,signal,signalEdge))



client.close()
