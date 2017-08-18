#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep,time
import traceback
import json

nodeid = sys.argv[1]
# ser = serial.Serial(port, 115200)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)

sock.connect(("localhost", 9000))

RUN_FOR_SECS = 60
start=time()
count=0
while True:
	try:
		# data = ser.readline()
		json_data ={}#'{"nodeid":' + nodeid', "value": "123456789012345678901234567890123456789012345678901234567890abcdxyz"}'
		json_data['nodeid'] = nodeid
		json_data['value'] = "123456789012345678901234567890123456789012345678901234567890abcdxyz"
		data_string = json.dumps(json_data)
		# print(data_string)
		# data = str.encode(nodeid + ",123456789012345678901234567890123456789012345678901234567890abcdxyz\n")
		sleep(0.00001)
		# print(data)
		# for i in range(100):
		sock.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
			# sock.flush()
			# sleep(0.001)
		count = count + 1
		if(time() - start > RUN_FOR_SECS): break
	except:
		traceback.print_exc()
		sock.close()
print("sent out:",count)
print("started",start)
print("ended",time())
