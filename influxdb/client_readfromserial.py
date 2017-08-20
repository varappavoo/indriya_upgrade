#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep
import traceback

nodeid = sys.argv[1]
port = sys.argv[2]
ser = serial.Serial(port, 115200)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 9000))

while True:
	try:
		data = ser.readline()
		#print(data)
		sock.send(nodeid + "," + data)
	except:
		traceback.print_exc()
		sock.close()

