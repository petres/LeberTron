from collections import deque
import serial, threading, time

"""
Find sonar delay threshold
try averageing multiple input values
keep track of states
assess different states
"""


SLIDING = True
SLIDING_WINDOW_SIZE = 8

STEARING = True
STEARING_L_MAX = 20
STEARING_I_MAX = 30
STEARING_R_MAX = 60

# if there is an object between, we shoot
SHOOT_MIN = 0
SHOOT_MAX = 70

state = 0
curr = 0
shoot = False

def inputRead():
	global curr, state

	sliding_window = deque()

	prevState = 0
	while not exitFlag:
		try:

			# CURRENT POSITION
			line = serialConn.readline().rstrip('\r\n')
			distances = line.split(" ")
			curr = int(distances[0])/90*2
			shoot_dist = distances[1]
			## SLIDING WINDOW
			## current value is based on last n
			if SLIDING:
				sliding_window.append(curr)
				if len(sliding_window) >= SLIDING_WINDOW_SIZE:
					sliding_window.popleft()
				curr = sum(sliding_window) / len(sliding_window)

			## STEARING
			## categorize in 3 steering states
			if STEARING:
				if curr <= STEARING_L_MAX:
					state = -1
					shoot = False
				elif curr > STEARING_L_MAX and curr <= STEARING_I_MAX:
					state = 0
					shoot = False
				elif curr > STEARING_I_MAX and curr <= STEARING_R_MAX:
					state = 1
					shoot = False
			# 	elif curr > STEARING_R_MAX:
			# 		state = 0
			# 		shoot = True
			if SHOOT_MIN <= shoot_dist <= SHOOT_MAX:
				shoot = True
			else:
				shoot = False
			# if state != prevState:
			#print state

			if shoot:
				print "Shoot!"

			# prevState = state


		except Exception, e:
			continue

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
