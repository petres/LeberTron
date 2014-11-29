#!/usr/bin/python
#
"""
Connect to robot
Provide API to write to robot
Provide listener thread
Disconnect gracefully

"""
import sys, serial, threading, time
from Queue import Queue


class BotComm():
	def __init__(self, serialPort, listenCallback, logFile = None):
		self.exitFlag 	= False
		self.ready 		= False
		self.logFile	= None
		self.pourQueue	= Queue()

		try:
			self.serialConn 	= serial.Serial(port = serialPort, timeout = 0, writeTimeout = 0)
			self.listenCallback = listenCallback
			self.listenThread 	= threading.Thread(target = self.callbackWrapper)
			self.listenThread.start()
		except Exception as e:
			sys.stderr.write(str(e) + '\n')

		if logFile is not None:
			sys.stderr.write("INFO: Open Logfile " + logFile + "\n")
			self.logFile = open(logFile, 'w', buffering = 0)


	def log(self, prefix, message):
		if self.logFile is not None:
			self.logFile.write(prefix + ": " + message + "\n")


	def close(self):
		self.exitFlag = True
		sys.stderr.write("INFO: Waiting for botComm listen thread ... ")
		self.listenThread.join()
		sys.stderr.write("DONE" + "\n")
		# time.sleep(0.2)
		self.serialConn.close()
		if self.logFile is not None:
			self.logFile.close()


	def callbackWrapper(self):
		serialBuffer = ""
		while not self.exitFlag:
			try:
				serialBuffer += self.serialConn.read(1)
				if (serialBuffer.endswith("\r\n")):
					command = serialBuffer.rstrip("\r\n")
					self.log("R", command + '\\r\\n')
					serialBuffer = ""

					commandList = command.split(" ")

					if commandList[0] == "READY":
						if int(commandList[2]) == 1:
							self.ready = True

					elif commandList[0] == "WAITING_FOR_CUP":
						pass
					elif commandList[0] == "POURING":
						pass
					elif commandList[0] == "ENJOY":
						pass
					elif commandList[0] == "ERROR":
						pass
					elif commandList[0] == "NOP":
						pass
					else:
						pass

					self.listenCallback(command)

				if not self.pourQueue.empty() and self.ready:
					self.pour(*self.pourQueue.get())
					self.ready = False

			except Exception as e:
				sys.stderr.write(str(e) + '\n')
				continue
			# finally:
			# 	time.sleep(0.1)


	def send(self, verb, *args):
		try:
			messageString = verb + " " + " ".join(str(n) for n in args)
			self.serialConn.write(messageString + '\r\n')
			self.log("T", messageString + '\\r\\n')
		except Exception as e:
			sys.stderr.write(str(e) + '\n')


	def pourBottle(self, bottleNr, amount):
		temp = [0] * 7
		temp[bottleNr] = amount
		self.pourQueue.put(temp)
		#self.pour(*temp)


	def pour(self, *args):
		sys.stderr.write("INFO: SEND POUR COMMAND (" + " ".join(str(n) for n in args) + ")")
		"""pour x_i grams of ingredient i, for i=1..n; will skip bottle
		if x_n < UPRIGHT_OFFSET"""
		# TODO: Check if ready for pour
		self.send("POUR", *args)
		self.ready = False


	def abort(self):
		"""abort current cocktail"""
		self.send("ABORT")


	def resume(self):
		"""resume after BOTTLE_EMPTY error, use this command when
		bottle is refilled"""
		self.send("RESUME")


	def dance(self):
		"""let the bottles dance!"""
		self.send("DANCE")


	def tare(self):
		"""sets scale to 0, make sure nothing is on scale when
		sending this command Note: taring is deleled, when Arduino
		is reseted (e.g. on lost serial connection)"""
		self.send("TARE")


	def turn(self, bottle_nr, microseconds):
		"""turns a bottle (numbered from 0 to 6) to a position
		given in microseconds"""
		self.send("TURN")


	def echo(self, msg):
		"""Example: ECHO ENJOY\r\n Arduino will then print "ENJOY"
		This is a workaround to resend garbled messages manually."""
		self.send("ECHO", msg)


	def nop(self):
		"""Arduino will do nothing and send message "DOING_NOTHING".
		This is a dummy message, for testing only."""
		self.send("NOP")


if __name__ == '__main__':
	def youGotMsg(msg):
		print msg

	c = BotComm('/dev/tty.usbmodem621', youGotMsg)
	while True:
		if c.ready:
			print "Ready"
			c.pour(str(10), str(10), str(10), str(10), str(10), str(10), str(10))

		# time.sleep(0.2)
