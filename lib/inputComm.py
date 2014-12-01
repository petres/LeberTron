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

    def __init__(self, serialPort='/dev/tty.usbserial-A9WFF5LH',
        slidingWindowSize = 3, twoSensors = False, shootMin = 5, shootMax = 20):

        self.exitFlag = False

        self.slidingWindow = deque()
        self.slidingWindowSize = slidingWindowSize

        self.shootMin = shootMin
        self.shootMax = shootMax

        # -1: left | 0: idle | 1: right
        # self.state = 0
        
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
            self.shoot = False
        
    def doThePosition(self, distance):
        if 0 < distance < 100:
            self.slidingWindow.append(distance)

        if len(self.slidingWindow) >= self.slidingWindowSize:
            self.slidingWindow.popleft()

        if len(self.slidingWindow) == 0:
            self.position = 0
        else:
            self.position = sum(self.slidingWindow) / len(self.slidingWindow)

    def doThePosition2(self, distance):


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
                    shootDistance = vals[0]
                    shootDistance = self.transformVal(shootDistance)

                    self.doTheShoot(shootDistance)

                else: 
                    distance = float(line)
                    distance = self.transformVal(distance)

                # Calculate current position with Sliding Window
                if self.sliding:
                    self.doThePosition(distance)
                else:
                    self.position = distance

                print self.position
            except Exception, e:
                continue


if __name__ == '__main__':

    s = InputComm(slidingWindowSize = 3)

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        s.close()
