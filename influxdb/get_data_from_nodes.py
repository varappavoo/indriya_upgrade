#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep,time

from multiprocessing import Process, Manager
import traceback
import json

from config import *

# dbhost = "192.168.1.103"
list_of_nodes={}
list_of_nodes_running=[]

# def stop_collection_from(nodeid, manager_proxy_nodes_status):
# 	# sleep(5)
# 	manager_proxy_nodes_status[nodeid]=False
	

def check_nodes_status_from_db(manager_proxy_nodes_status):
	################
	# start n stop collection based on status from db
	################
	# static test for now
	################
	
	# nodes_status = list_of_nodes
	while(True):
		# list_of_nodes = {}
		print("1")
		nodes_status_file = open("db_nodes.csv",'r')
		line = nodes_status_file.readline() # header
		line = nodes_status_file.readline()
		print("2")
		while(line!=""):
			line_split = line.split(",")
			print(line_split)
			nodeid = line_split[0]
			list_of_nodes[nodeid] = {}
			list_of_nodes[nodeid]['gateway_ip'] = line_split[1]
			list_of_nodes[nodeid]['gateway_port'] = int(line_split[2])
			list_of_nodes[nodeid]['active'] = int(line_split[3])
			line = nodes_status_file.readline()

		print(list_of_nodes)
		print(list_of_nodes_running)

		for nodeid in list_of_nodes.keys():
			print(nodeid, list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port'])
			manager_proxy_nodes_status[nodeid] = list_of_nodes[nodeid]['active']
			if not list_of_nodes[nodeid]['active'] and nodeid in list_of_nodes_running:
				list_of_nodes_running.remove(nodeid)
			if list_of_nodes[nodeid]['active'] and nodeid not in list_of_nodes_running:
				list_of_nodes_running.append(nodeid)
				server = Process(target=start_collection_from,args=([nodeid,manager_proxy_nodes_status]))
				server.start()
		print(manager_proxy_nodes_status)

		sleep(5)
		# server = Process(target=stop_collection_from,args=(['111',manager_proxy_nodes_status]))
		# server.start()
		# sleep(5)

	# manager_proxy_nodes_status['111']=True
	# print(manager_proxy_nodes_status)
	# server = Process(target=start_collection_from,args=(['111',manager_proxy_nodes_status]))
	# server.start()
	# pass


def start_collection_from(nodeid, manager_proxy_nodes_status):
	sock_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_node.connect((list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port']))

	# sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	# sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	# sock_server.connect((server_ip, server_savetodb_port))

	sock_aggr_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_aggr_server.connect((server_aggr_ip, server_aggr_port))

	sock_rt_stream_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	
	# TCP_IP = '0.0.0.0'
	# TCP_PORT = 9000 + int(nodeid)
	# sock_dup = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock_dup.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# sock_dup.bind((TCP_IP, TCP_PORT))
	# sock_dup.listen(100)
	# (client_sock_dub, (ip,port)) = tcpServer.accept()

	last_dangling_chunk = ""

	count=0
	while True:
		if(manager_proxy_nodes_status[nodeid]):

			print("PROCESS","manager_proxy_nodes_status['111']",manager_proxy_nodes_status['111'])

			# print("connecting to node", nodeid)
			try:
				data_received = sock_node.recv(4096)
				if not data_received: break
				# data_received = data_received

				data_received_split = data_received.decode('utf-8','ignore').split('\n')
				# data_received_split = data_received.split('\n')
				for i in range(len(data_received_split) - 1): # last chunk is likely to be incomplete
					json_data ={}#'{"nodeid":' + nodeid', "value": "123456789012345678901234567890123456789012345678901234567890abcdxyz"}'
					count = count + 1
					json_data['nodeid'] = nodeid
					if i == 0: 
						json_data['value'] = last_dangling_chunk + data_received_split[0]
					else:
						json_data['value'] = data_received_split[i]

					data_string = json.dumps(json_data)
					print(data_string)
					# sock_server.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
					sock_aggr_server.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
					sock_rt_stream_udp.sendto(str.encode(data_string,'utf-8') + str.encode("\n"), ('localhost', UDP_PORT+int(nodeid)))
					print(UDP_PORT+int(nodeid))
				last_dangling_chunk = data_received_split[-1]
			except:
				print(traceback.print_exc())
		else:
			break

	print("closing socket to server and node", nodeid)
	# sleep(5)
	list_of_nodes_running.remove(nodeid)
	sock_aggr_server.close()
	sock_node.close()






with Manager() as manager:

	manager_proxy_nodes_status = manager.dict()

	server = Process(target=check_nodes_status_from_db,args=([manager_proxy_nodes_status]))
	server.start()


	# server.join()

	while True:
		sleep(5)


	# sleep(5)
	
	# dict_proxy = manager.list()
	# dict_proxy.append({})

	# manager_proxy_nodes_status = dict_proxy[0]
	# manager_proxy_nodes_status['111']=True

	# dict_proxy = manager_proxy_nodes_status
	# print(manager_proxy_nodes_status)

	# print("MAIN","manager_proxy_nodes_status['111']",manager_proxy_nodes_status['111'])



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
