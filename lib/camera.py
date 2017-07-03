#from imutils import contours
#from skimage import measure
#import numpy as np
from multiprocessing import Process, Value
import time

class Camera(object):
    def __init__(self, device = 1, treshold = 250, blurRadius = 11, resolution = (160, 120)):
        self.device = device
        self.treshold = treshold
        self.blurRadius = blurRadius
        self.resolution = resolution
        self.exitFlag = False
        logging.debug("CAMERA " + " ".join( list(map(lambda x: str(x), [device, treshold, blurRadius, resolution]))))

        self.position = Value('d', 0.5)
        self.exitFlag = Value('i', 0)

        self.p = Process(target=self.trackPositionCallback, args=(self.position, self.exitFlag))
        self.p.start()

    def trackPositionCallback(self, position, exitFlag):
        logging.debug("Camera: Thread started")
        import cv2

        cap = cv2.VideoCapture(self.device)

        cap.set(3, self.resolution[0])
        cap.set(4, self.resolution[1])

        while self.exitFlag.value == 0:
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (self.blurRadius, self.blurRadius), 0)
                thresh = cv2.threshold(blurred, self.treshold, 255, cv2.THRESH_BINARY)[1]
                #thresh = cv2.erode(thresh, None, iterations=2)
                #thresh = cv2.dilate(thresh, None, iterations=4)
                m = cv2.moments(thresh)
                if m['m00'] != 0:
                    #print("x = " + str(m['m10']/m['m00']))
                    #print("y = " + str(m['m01']/m['m00']))

                    position.value = m['m10']/m['m00']/self.resolution[0]
                    logging.debug("Camera: Setting position to " + str(position.value))
                else:
                    logging.debug("Camera: No object found")


                # Display the resulting fram
                # cv2.imshow('frame1', frame)
                # cv2.imshow('frame2', blurred)
                # cv2.imshow('frame3', thresh)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
            else:
                logging.debug("Camera: Can not read ")

            time.sleep(0.05)


        # When everything done, release the capture
        cap.release()

    def close(self):
        self.exitFlag.value = 1
        logging.info("INFO: Waiting for camera listen thread ... ")
        self.p.join()
        logging.info("DONE" + "\n")

if __name__ == '__main__':
    class logging():
        @staticmethod
        def debug(s):
            print s
        @staticmethod
        def info(s):
            print s
    c = Camera(device = 1)
    try:
        while True:
            #print c.position.value
            time.sleep(0.1)
    except KeyboardInterrupt:
        c.close()
else:
    import logging
