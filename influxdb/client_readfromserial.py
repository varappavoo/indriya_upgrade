#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep
import traceback

port = sys.argv[1]
ser = serial.Serial(port, 115200)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 9000))

while True:
	try:
		data = ser.readline()
		print(data)
		# for i in range(100):
		sock.send(data)# + str.encode("\n")) # encode to from str to byte
			# sock.flush()
			# sleep(0.001)
	except:
		traceback.print_exc()
		sock.close()

