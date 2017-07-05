from multiprocessing import Process, Value
import time
import cv2
import logging
#import numpy as np

class Camera(object):
    def __init__(self, device = 1, threshold = 250, blurRadius = 11, resolution = (160, 120), show = False):
        self.device = device
        self.threshold = threshold
        self.blurRadius = blurRadius
        self.resolution = resolution
        self.exitFlag = False
        #logging.info("CAMERA " + " ".join( list(map(lambda x: str(x), [device, threshold, blurRadius, resolution]))))

        self.position = Value('d', 0.5)
        self.exitFlag = Value('i', 0)
        self.show = show

        if not show:
            self.p = Process(target=self.trackPositionCallback, args=(self.position, self.exitFlag))
            self.p.start()
        else:
            self.trackPositionCallback(self.position, self.exitFlag)

    def trackPositionCallback(self, position, exitFlag):
        if not self.show:
            logging.info("Camera: Thread started")
            import signal
            signal.signal(signal.SIGINT, signal.SIG_IGN)

        cap = cv2.VideoCapture(self.device)

        cap.set(3, self.resolution[0])
        cap.set(4, self.resolution[1])

        while self.exitFlag.value == 0:
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (self.blurRadius, self.blurRadius), 0)
                thresh = cv2.threshold(blurred, self.threshold, 255, cv2.THRESH_BINARY)[1]
                #thresh = cv2.erode(thresh, None, iterations=2)
                #thresh = cv2.dilate(thresh, None, iterations=4)
                m = cv2.moments(thresh)
                if m['m00'] != 0:
                    #print("x = " + str(m['m10']/m['m00']))
                    #print("y = " + str(m['m01']/m['m00']))
                    tmp = m['m10']/m['m00']
                    position.value = tmp/self.resolution[0]
                    logging.debug("Camera: Setting position to " + str(position.value) + " (value: " + str(tmp) + ", resolutionX: " + str(self.resolution[0]) + ")")
                else:
                    logging.info("Camera: No object found")

                if self.show:
                    cv2.imshow('frame1', frame)
                    cv2.imshow('frame2', blurred)
                    cv2.imshow('frame3', thresh)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            else:
                logging.info("Camera: Can not read ")

            time.sleep(0.05)

        logging.info("INFO: Camera process stopping ... ")

        # When everything done, release the capture
        cap.release()

    def close(self):
        self.exitFlag.value = 1
        logging.info("INFO: Waiting for camera listen thread ... ")
        self.p.join()
        logging.info("DONE" + "\n")

if __name__ == '__main__':
    import sys
    from ConfigParser import SafeConfigParser

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(levelname)8s - %(asctime)s: %(message)s')

    show = len(sys.argv) > 1 and sys.argv[1] == "imshow"
    controllerConfig = SafeConfigParser()
    controllerConfig.read('./etc/controller.cfg')
    #CameraController.mirror =  controllerConfig.getboolean('Camera', 'mirror')
    camera = Camera(device = controllerConfig.getint('Camera', 'device'), threshold = controllerConfig.getint('Camera', 'threshold'),
                                  resolution = (controllerConfig.getint('Camera', 'resolutionX'), controllerConfig.getint('Camera', 'resolutionY')),
                                  blurRadius = controllerConfig.getint('Camera', 'blurRadius'), show = show)

    if not show:
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            camera.close()
