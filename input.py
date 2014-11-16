from collections import deque
import serial, threading, time

"""
Find sonar delay threshold
try averageing multiple input values
keep track of states
assess different states
"""


SLIDING = True
SLIDING_WINDOW_SIZE = 20

STEARING = True
STEARING_L_MAX = 20
STEARING_I_MAX = 30
STEARING_R_MAX = 60

state = 0
curr = 0

def inputRead():
	global curr, state

	sliding_window = deque()

	while not exitFlag:
		try:
			# CURRENT POSITION
			line = serialConn.readline().rstrip('\r\n')
			curr = int(line)

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
				elif curr > STEARING_L_MAX and curr <= STEARING_I_MAX:
					state = 0
				elif curr > STEARING_I_MAX and curr <= STEARING_R_MAX:
					state = 1

			

		except Exception, e:
			continue

	serialConn.close()

def main():
	threadRead.start()

# Init Threads
threadRead = threading.Thread(target = inputRead)
exitFlag = 0 # Exit main

# Init Serial Connections
serialConn = serial.Serial('/dev/tty.usbserial-A9WFF5LH', 9600)

if __name__ == '__main__':
	main()
	try:
		while True:
			time.sleep(0.2)
	except KeyboardInterrupt:
		exitFlag = 1
		threadRead.join()
		print "Ciao..."
