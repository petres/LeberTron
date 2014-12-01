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
        sliding = False, slidingWindowSize = 3, transform = False,
        twoSensors = False, shootMin = 5, shootMax = 20):

        self.exitFlag = False
        self.slidingWindow = deque()
        self.slidingWindowSize = slidingWindowSize

        # if there is an object between, we shoot
        self.shoot = False
        self.shootMin = shootMin
        self.shootMax = shootMax

        # -1: left | 0: idle | 1: right
        self.state = 0
        self.position = 0

        self.serialConn = False
        self.readThread = False

        self.transform = transform
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


    def doTheShoot(self, distance):
        if self.shootMin <= distance <= self.shootMax:
            self.shoot = True
        else:
            self.shoot = False
        
    def doTheSlide(self, distance):
        if 0 < distance < 100:
            self.slidingWindow.append(distance)
        if len(self.slidingWindow) >= self.slidingWindowSize:
            self.slidingWindow.popleft()
        if len(self.slidingWindow) == 0:
            self.position = 0
        else:
            self.position = sum(self.slidingWindow) / len(self.slidingWindow)

    def transformVal(self, serialInput):
        return float(serialInput) / 90 * 2

    def readInputCallback(self):
        while not self.exitFlag:

            # CURRENT POSITION
            # import ipdb; ipdb.set_trace()
            try:
                line = self.serialConn.readline().rstrip('\r\n')
                logging.debug("LINE from Arduino: '%s'" % line)

                if self.twoSensors:
                    vals = line.split(" ")
                    distance = float(vals[0])
                    shootDistance = float(vals[0])
                    if self.transform:
                        distance = self.transformVal(distance)
                        shootDistance = self.transformVal(shootDistance)
                else: 
                    distance = float(line)
                    if self.transform:
                        distance = self.transform

                self.doTheSlide(distance)

                # distanceAndShoot = self.readShootAndDistance(line)
                # self.doTheShoot(shootDistance)

                print self.position
            except Exception, e:
                raise e


if __name__ == '__main__':

    s = InputComm()

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        s.close()
