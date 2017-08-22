#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep,time

import multiprocessing
import traceback
import json

from nodes_db import *

server_ip = "192.168.1.102"
server_port = 9000
# dbhost = "192.168.1.103"

def get_data_from(nodeid, list_of_nodes):
	sock_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_node.connect((list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port']))

	sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_server.connect((server_ip, server_port))

	last_dangling_chunk = ""

	count=0
	while list_of_nodes[nodeid]['active']:
		try:
			data_received = sock_node.recv(4096)
			if not data_received: break
			data_received_split = data_received.decode('utf-8').split('\n')
			for i in range(len(data_received_split) - 1): # last chunk is likely to be incomplete
				json_data ={}#'{"nodeid":' + nodeid', "value": "123456789012345678901234567890123456789012345678901234567890abcdxyz"}'
				count = count + 1
				json_data['nodeid'] = nodeid
				if i == 0: 
					json_data['value'] = last_dangling_chunk + data_received_split[0]
				else:
					json_data['value'] = data_received_split[i]

				data_string = json.dumps(json_data)
				sock_server.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte

		except:
			print(traceback.print_exc())
	print("closing socket to server and node", nodeid)
	sock_server.close()
	sock_node.close()


print(list_of_nodes)

for nodeid in list_of_nodes.keys():
	print(nodeid, list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port'])
	if list_of_nodes[nodeid]['active']:
		server = multiprocessing.Process(target=get_data_from,args=([nodeid,list_of_nodes]))
		server.start()




# nodeid = sys.argv[1]

# # ser = serial.Serial(port, 115200)
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
# sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)

# sock.connect((host, 9000))

# RUN_FOR_SECS = 4*60*60
# ### 900 = 15mins
# # time count_value
# # ---- -----------
# # 0    12430000
# # 12430000/(900*100)
# # 138.11111111111111

# start=time()
# count=0
# while True:
# 	try:
# 		# data = ser.readline()
# 		json_data ={}#'{"nodeid":' + nodeid', "value": "123456789012345678901234567890123456789012345678901234567890abcdxyz"}'
# 		json_data['nodeid'] = nodeid
# 		json_data['value'] = "123456789012345678901234567890123456789012345678901234567890abcdxyz"
# 		data_string = json.dumps(json_data)
# 		# print(data_string)
# 		# data = str.encode(nodeid + ",123456789012345678901234567890123456789012345678901234567890abcdxyz\n")
# 		# sleep(0.001)
# 		# print(data)
# 		# for i in range(100):
# 		sock.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
# 			# sock.flush()
# 			# sleep(0.001)
# 		count = count + 1
# 		if(time() - start > RUN_FOR_SECS): break
# 	except:
# 		traceback.print_exc()
# 		sock.close()
# print("sent out:",count)
# print("started",start)
# print("ended",time())
