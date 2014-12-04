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
        shootMin = 0, shootMax = 20, median = True):

        self.distanceMin = distanceMin - 10
        self.distanceMax = distanceMax + 10

        self.exitFlag = False
        self.sliding = sliding

        self.slidingWindow = deque()
        self.slidingWindowSize = slidingWindowSize
        self.median = True

        self.shootPosition = False
        self.bullets = 0

        self.shootMin = shootMin
        self.shootMax = shootMax

        # -1: left | 0: idle | 1: right
        self.state = 0

        self.position = 0

        self.twoSensors = twoSensors

        try:
            self.serialConn = serial.Serial(serialPort, 9600)
            self.readThread = threading.Thread(target=self.readInputCallback)
            self.bulletLock = threading.Lock()
            self.readThread.start()
        except Exception as e:
            logging.error("Problem in InputComm: '%s'" % str(e))
            raise e

    def close(self):
        if self.bulletLock.locked():
            self.bulletLock.release()
        self.exitFlag = True
        logging.info("INFO: Waiting for inputComm listen thread ... ")
        self.readThread.join()
        logging.info("DONE" + "\n")
        self.serialConn.close()

    def fetchBullet(self):
        ret = False
        self.bulletLock.acquire()
        if (self.bullets > 0):
            self.bullets -= 1
            ret = True
        self.bulletLock.release()
        return ret


    def doTheShoot(self, shootDistance):
        if self.shootMin <= shootDistance <= self.shootMax:
            if not self.shootPosition:
                self.bulletLock.acquire()
                self.bullets += 1
                self.bulletLock.release()
            self.shootPosition = True
        else:
            self.shootPosition = False

    def getPositionDirect(self, distance):
        if self.distanceMin < distance < self.distanceMax:
            self.slidingWindow.append(distance)

        if len(self.slidingWindow) > self.slidingWindowSize:
            self.slidingWindow.popleft()

        if len(self.slidingWindow) < self.slidingWindowSize:
            return (self.distanceMin + self.distanceMax)/2

        if self.median:
            sortList = sorted(self.slidingWindow)
            return sortList[int(self.slidingWindowSize / 2)]
        else:
            return sum(self.slidingWindow) / len(self.slidingWindow)


    def getPositionAdjusted(self, distance):
        tolerance = 1.5
        movement = 0.4

        positionSensor = self.getPositionDirect(distance)
        if positionSensor > self.position + tolerance:
            return self.position + movement
        elif positionSensor < self.position - tolerance:
            return self.position - movement
        return self.position


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
                    self.position = self.getPositionAdjusted(distance)
                    logging.debug("Slided Position from Arduino: '%s'" % self.position)
                else:
                    self.position = distance

            except Exception, e:
                logging.error("Problem in Arduino Read: '%s'" % str(e))
                continue


if __name__ == '__main__':
    s = InputComm(serialPort="/dev/tty.usbmodem411", slidingWindowSize = 3, twoSensors = True, sliding = True)
    try:
        while True:
            print s.position, s.bullets
            time.sleep(0.1)
    except KeyboardInterrupt:
        s.close()
