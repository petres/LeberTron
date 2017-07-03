#from imutils import contours
#from skimage import measure
import numpy as np
import cv2
import threading
import logging
import time


class Camera():
    def __init__(self, device = 1, treshold = 250, blurRadius = 11, resolution = (160, 120)):
        self.device = device
        self.treshold = treshold
        self.blurRadius = blurRadius
        self.resolution = resolution
        self.exitFlag = False
        self.position = 0
        logging.debug("CAMERA " + " ".join( list(map(lambda x: str(x), [device, treshold, blurRadius, resolution]))))



        try:
            self.readThread = threading.Thread(target=self.trackPositionCallback)
            self.readThread.start()
        except Exception as e:
            logging.error("Problem in Camera: '%s'" % str(e))
            raise e

    def trackPositionCallback(self):
        self.cap = cv2.VideoCapture(self.device)

        self.cap.set(3, self.resolution[0])
        self.cap.set(4, self.resolution[1])
        while not self.exitFlag:
            # Capture frame-by-frame
            ret, frame = self.cap.read()

            # Our operations on the frame come here
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (self.blurRadius, self.blurRadius), 0)
            thresh = cv2.threshold(blurred, self.treshold, 255, cv2.THRESH_BINARY)[1]
            #thresh = cv2.erode(thresh, None, iterations=2)
            #thresh = cv2.dilate(thresh, None, iterations=4)
            m = cv2.moments(thresh)
            if m['m00'] != 0:
                #print("x = " + str(m['m10']/m['m00']))
                #print("y = " + str(m['m01']/m['m00']))

                self.position = m['m10']/m['m00']/self.resolution[0]
                logging.debug("Camera: Setting position to " + str(self.position))
            else:
                logging.debug("Camera: No object found")


            # Display the resulting fram
            # cv2.imshow('frame1', frame)
            # cv2.imshow('frame2', blurred)
            # cv2.imshow('frame3', thresh)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # When everything done, release the capture
        cap.release()

    def close(self):
        self.exitFlag = True
        logging.info("INFO: Waiting for camera listen thread ... ")
        self.readThread.join()
        logging.info("DONE" + "\n")

if __name__ == '__main__':
    c = Camera(device = 1)
    try:
        while True:
            print c.position
            time.sleep(0.1)
    except KeyboardInterrupt:
        c.close()
