from collections import deque
import serial
import threading
import time
import sys
import logging


"""
Find sonar delay threshold
try averageing multiple input values
keep track of states
assess different states
"""

class InputComm():

    def __init__(self, serialPort='/dev/tty.usbserial-A9WFF5LH', distanceMin = 5, 
        distanceMax = 30, sliding = True, slidingWindowSize = 15, twoSensors = False, 
        shootMin = 5, shootMax = 20):

        self.distanceMin = distanceMin
        self.distanceMax = distanceMax

        self.exitFlag = False
        self.sliding = sliding

        self.slidingWindow = deque()
        self.slidingWindowSize = slidingWindowSize

        self.shoot = False
        self.bullet = True
        self.shootMin = shootMin
        self.shootMax = shootMax

        # -1: left | 0: idle | 1: right
        self.state = 0
        
        self.position = 0

        self.twoSensors = twoSensors

        try:
            self.serialConn = serial.Serial(serialPort, 9600)
            self.readThread = threading.Thread(target=self.readInputCallback)
            self.readThread.start()
        except Exception, e:
            raise e

    def close(self):
        self.exitFlag = True
        logging.info("INFO: Waiting for inputComm listen thread ... ")
        self.readThread.join()
        logging.info("DONE" + "\n")
        self.serialConn.close()

    def doTheShoot(self, shootDistance):
        if self.shootMin <= shootDistance <= self.shootMax:
            self.shoot = True
        else:
            #self.bullet = True
            self.shoot = False


        
    def doThePosition(self, distance):
        if self.distanceMin < distance < self.distanceMax:
            self.slidingWindow.append(distance)
        else:
            return            

        if len(self.slidingWindow) >= self.slidingWindowSize:
            self.slidingWindow.popleft()

        if len(self.slidingWindow) == 0:
            self.position = 0
        else:
            self.position = sum(self.slidingWindow) / len(self.slidingWindow)

    def doThePosition2(self, distance):
        prevPos = self.position
        self.doThePosition(distance)
        if prevPos < self.position:
            self.position -= 0.1
        elif prevPos > self.position:
            self.position += 0.1 



    def transformVal(self, serialInput):
        return float(serialInput) / 90 * 2

    def readInputCallback(self):
        while not self.exitFlag:

            # CURRENT POSITION

            try:
                # Read Arduino
                line = self.serialConn.readline().rstrip('\r\n')
                logging.debug("LINE from Arduino: '%s'" % line)
                
                if self.twoSensors:
                    vals = line.split(" ")
                    distance = vals[0]
                    distance = self.transformVal(distance)
                    shootDistance = vals[1]
                    shootDistance = self.transformVal(shootDistance)
                    self.doTheShoot(shootDistance)
                else: 
                    distance = float(line)
                    distance = self.transformVal(distance)

                # Calculate current position with Sliding Window
                if self.sliding:
                    self.doThePosition2(distance)
                    logging.debug("Slided Position from Arduino: '%s'" % self.position)
                else:
                    self.position = distance

            except Exception, e:
                logging.error("Problem in Arduino Read: '%s'" % str(e))
                continue


if __name__ == '__main__':

    s = InputComm(serialPort="/dev/tty.usbmodem411", slidingWindowSize = 3, twoSensors = True)

    try:
        while True:
            print s.position, s.shoot
            time.sleep(0.1)
    except KeyboardInterrupt:
        s.close()
