from multiprocessing import Process, Value
from collections import deque
import time
import cv2
import logging
#import numpy as np

class Camera(object):
    def __init__(self, device = 1, threshold = 250, blur_radius = 11, resolution_x = 160, resolution_y = 120,
                 sliding_window_size = 5, shoot_type = None, sliding_window_shoot_size = 9, shoot_height = 5,
                 show = "false", controller = None):
        self.device = int(device)
        self.blurRadius = int(blur_radius)
        self.resolution = (int(resolution_x), int(resolution_y))
        self.exitFlag = False
        self.controller = controller

        self.show = show == "true"
        self.shootType = shoot_type
        self.shootHeight = int(shoot_height)

        self.slidingWindowSize = int(sliding_window_size)
        self.slidingWindowShootSize = int(sliding_window_shoot_size)

        self.position = Value('d', 0.5)
        self.shootFlag = Value('i', 0)
        self.exitFlag = Value('i', 0)
        self.threshold = Value('i', int(threshold))

        self.p = Process(target=self.trackPositionCallback, args=(self.position, self.shootFlag, self.threshold, self.exitFlag))
        self.p.start()

    def getPosition(self):
        return self.position.value

    def getInput(self, c):

        if self.shootFlag.value == 1:
            self.shootFlag.value == 0
            return self.controller.SHOOT

        if c == ord('n'):
            self.threshold.value = self.threshold.value + 1
            logging.info("Camera: Setting threshold to " + str(self.threshold.value))
        elif c == ord('m'):
            self.threshold.value = self.threshold.value - 1
            logging.info("Camera: Setting threshold to " + str(self.threshold.value))

    def trackPositionInit(self):
        logging.info("Camera: Process started")
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        if self.slidingWindowSize > 0:
            self.slidingWindow = deque()
            for i in range(self.slidingWindowSize):
                self.slidingWindow.append(self.position.value)

        if self.shootType == "jump":
            self.slidingWindowShoot = deque()

        self.cap = cv2.VideoCapture(self.device)

        self.cap.set(3, self.resolution[0])
        self.cap.set(4, self.resolution[1])

    def trackPositionCallback(self, position, shootFlag, threshold, exitFlag):
        self.trackPositionInit()

        avg = None

        while self.exitFlag.value == 0:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (self.blurRadius, self.blurRadius), 0)
                thresh = cv2.threshold(blurred, self.threshold.value, 255, cv2.THRESH_BINARY)[1]
                #thresh = cv2.erode(thresh, None, iterations=2)
                #thresh = cv2.dilate(thresh, None, iterations=4)
                m = cv2.moments(thresh)
                if m['m00'] != 0:
                    #print("x = " + str(m['m10']/m['m00']))
                    #print("y = " + str(m['m01']/m['m00']))
                    tmpX = m['m10']/m['m00']
                    tmpX01 = tmpX/self.resolution[0]

                    tmpY = m['m01']/m['m00']
                    tmpY01 = tmpY/self.resolution[1]

                    if self.shootType == "jump":
                        self.slidingWindowShoot.append(tmpY01)
                        if len(self.slidingWindowShoot) > self.slidingWindowShootSize:
                            self.slidingWindowShoot.popleft()
                        sortList = sorted(self.slidingWindowShoot)
                        avg = sortList[int(len(self.slidingWindowShoot) / 2)]
                        if tmpY01 < avg - 0.01*self.shootHeight:
                            #print "SHOOT"
                            shootFlag.value = 1
                        else:
                            shootFlag.value = 0

                    if self.slidingWindowSize > 1:
                        self.slidingWindow.popleft()
                        self.slidingWindow.append(tmpX01)
                        sortList = sorted(self.slidingWindow)
                        position.value = sortList[int(self.slidingWindowSize / 2)]
                    else:
                        position.value = tmpX01

                    #logging.debug("Camera: POS: " + str(position.value) + ", TMP: " + str(tmpX01) + ", ORG: " + str(tmpX))
                else:
                    logging.info("Camera: No object found")

                if self.show:
                    thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
                    offset = int(0.01*self.controller.margin*self.resolution[0])
                    for i in [frame, blurred, thresh]:
                        cv2.line(i, (offset, 0), (offset, self.resolution[1]), (255,0,0), 2)
                        cv2.line(i, (self.resolution[0] - offset, 0), (self.resolution[0] - offset, self.resolution[1]), (255,0,0), 2)
                    cv2.imshow('Original', frame)
                    cv2.imshow('Blurred', blurred)

                    if m['m00'] != 0:
                        cv2.circle(thresh, (int(tmpX), int(tmpY)), 10, (0,255,0), -1)

                    if self.shootType == "jump" and avg is not None:
                        h = int((avg - 0.01*self.shootHeight)*self.resolution[1])
                        cv2.line(thresh, (int(tmpX) - 20, h), (int(tmpX) + 20, h), (0, 0, 255), 2)

                    if position.value is not None:
                        cv2.circle(thresh, (int(position.value * self.resolution[0]), self.resolution[1] - 10), 10, (0, 0 ,255), -1)


                    cv2.imshow('Threshold', thresh)

                    cv2.waitKey(1)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
            else:
                logging.info("Camera: Can not read ")

            time.sleep(0.01)

        logging.info("INFO: Camera process stopping ... ")

        # When everything done, release the capture
        self.cap.release()

    def close(self):
        self.exitFlag.value = 1
        logging.info("INFO: Waiting for camera listen thread ... ")
        self.p.join()
        logging.info("DONE" + "\n")

if __name__ == '__main__':
    import sys
    from ConfigParser import SafeConfigParser

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(message)s')

    controllerConfig = SafeConfigParser()
    controllerConfig.read('./etc/controller.cfg')
    kwargs = dict(controllerConfig.items("Camera"))
    camera = Camera(**kwargs)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        camera.close()
