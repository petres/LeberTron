from collections import deque
import serial, threading, time, sys


"""
Find sonar delay threshold
try averageing multiple input values
keep track of states
assess different states
"""


SLIDING = True
SLIDING_WINDOW_SIZE = 15


# if there is an object between, we shoot
SHOOT_MIN = 5
SHOOT_MAX = 20

state = 0
curr = 0
currA = 0
shoot = False
shootDist = 0

def inputRead():
	global curr, state, currA, shoot

	sliding_window = deque()

	prevState = 0
	while not exitFlag:
		# CURRENT POSITION
		#import ipdb; ipdb.set_trace()
		line = serialConn.readline().rstrip('\r\n')
		distances = line.split(" ")
		#sys.stderr.write("LINE from Arduino: '%s'" %line)
		try:
			currA = float(distances[0])/90*2
		except ValueError as e:
			continue

		sys.stderr.write("Received: " + str(distances) + "\n")

		try:
			shootDist = float(distances[1])/90*2
		except ValueError as e:

			shootDist = 0

		if SLIDING:
			if 0 < currA < 100:
				sliding_window.append(currA)
			if len(sliding_window) >= SLIDING_WINDOW_SIZE:
				sliding_window.popleft()
			if len(sliding_window) == 0:
				curr = 0
			else:
				curr = sum(sliding_window) / len(sliding_window)


		if SHOOT_MIN <= shootDist <= SHOOT_MAX:
			shoot = True
		else:
			shoot = False

	serialConn.close()

def start():
	threadRead.start()

# Init Threads
threadRead = threading.Thread(target = inputRead)
exitFlag = 0 # Exit main

# Init Serial Connections
serialConn = None

# def connect(serialPort = '/dev/ttyACM0'):
def connect(serialPort = '/dev/tty.usbserial-A9WFF5LH'):
	global serialConn
	serialConn = serial.Serial(serialPort, 9600)

if __name__ == '__main__':
	connect(serialPort = '/dev/ttyACM0')
	start()
	try:
		while True:
			time.sleep(0.2)
	except KeyboardInterrupt:
		exitFlag = 1
		threadRead.join()
		#print "Ciao..."
