from collections import deque
import serial, threading, time

# Left -1, Idle 0, Right 1
L_MAX = 20
I_MAX = 40
R_MAX = 60
state = 0
inputBufLock = threading.Lock()
inputBuf = deque()
exitFlag = 0

def inputLogic():
	"""Evaluate input buffer. Define three ranges
	left, idle, right. """
	global state

	while not exitFlag:
		if len(inputBuf) < 1:
			time.sleep(0.15)
			continue
	
		inputBufLock.acquire()
		curr = inputBuf.popleft()
		inputBufLock.release()

		prevState = state
		if curr <= L_MAX:
			state = -1
		elif curr > L_MAX and curr <= I_MAX:
			state = 0
		elif curr > I_MAX and curr <= R_MAX:
			state = 1

		if prevState != state:
			print state

def main():
	global exitFlag

	t1 = threading.Thread(target = inputLogic)
	t1.start()

	# Init Serial
	ser = serial.Serial('/dev/tty.usbserial-A9WFF5LH', 9600)

	# Write all values into a buffer
	while True:
		try:
			time.sleep(0.2)
			inputBufLock.acquire()
			distance = ser.readline().rstrip('\r\n')
			inputBuf.append(int(distance))
		except KeyboardInterrupt:
			break
		finally:
			if inputBufLock.locked():
				inputBufLock.release()

	# Tell other thread to exit and join
	exitFlag = 1
	t1.join()

	# Close serial 
	ser.close()
	print "Bye bye..."

if __name__ == '__main__':
	main()