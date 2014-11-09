from collections import deque
import serial, threading, time, sys

# Left -1, Idle 0, Right 1
L_MAX = 30
#I_MAX = 30
R_MAX = 50
state = 0
inputBufLock = threading.Lock()
inputBuf = deque()
exitFlag = 0

curr = 0

def inputRead():
	global curr, state
	# Init Serial
	ser = serial.Serial('/dev/ttyACM0', 9600)
	acc = 0

	# Write all values into a buffer
	while not exitFlag:
		try:
			s = ser.readline().rstrip('\r\n')
			next = int(s)
		except Exception as e:
			print >> sys.stderr, "not int:", s
			continue
		acc = (next + 9*acc) / 10.0;
		curr = int(acc / 2.0 / 29.1)
		if curr <= L_MAX:
			state = -1
		elif curr > R_MAX:
			state = 1
		else:
			state = 0


def main():
	global exitFlag

	t1 = threading.Thread(target = inputRead)
	t1.start()

	#t2 = threading.Thread(target = inputLogic)
	#t2.start()



	# t1.join()

	# # Close serial 
	# ser.close()
	# print "Bye bye..."

if __name__ == '__main__':
	main()