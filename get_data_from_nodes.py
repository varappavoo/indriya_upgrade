#!/usr/bin/python3
import serial
import socket
import sys
from time import sleep,time

from multiprocessing import Process, Manager
import traceback
import json

import logging

from config import *
# from active_users import *

#!/usr/bin/python3
import logging
import logging.config
#from logging.handlers import RotatingFileHandler
import fasteners

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('get_data')



# dbhost = "192.168.1.103"
# list_of_nodes={}
# list_of_nodes_running=[]

with open('nodes_virt_id_phy_id.json') as json_data:
	json_nodes_virt_id_phy_id = json.load(json_data)

def check_nodes_status_from_db(manager_proxy_nodes_status, active_users):
	################
	# start n stop collection based on status from db
	################
	# static test for now
	################
	

	# global active_users

	test_count=0
	while (True):
		active_motes = [value for values in active_users.values() for value in values]

		for nodeid in manager_proxy_nodes_status.keys():
			if nodeid not in active_motes:
				manager_proxy_nodes_status[nodeid] = INACTIVE

		# print("-------------------------------------------------------------------------")
		# print(active_users)
		# print("-------------------------------------------------------------------------")
		for nodeid in active_motes:
			if manager_proxy_nodes_status.get(nodeid) == None or manager_proxy_nodes_status[nodeid] != ACTIVE: # still inactive
				if json_nodes_virt_id_phy_id.get(nodeid) != None:
					gateway = json_nodes_virt_id_phy_id[nodeid]['gateway']
					port = json_nodes_virt_id_phy_id[nodeid]['port']
					server = Process(target=start_collection_from,args=([nodeid,gateway,port,manager_proxy_nodes_status]))
					# server = Process(target=start_collection_from,args=([nodeid,manager_proxy_nodes_status]))
					server.start()
					manager_proxy_nodes_status[nodeid] = ACTIVE
				else:
					logger.error("NODEID (" + nodeid + ") not found to determine GATEWAY:PORT")

		sleep(1)
		# test_count = test_count + 1
		# if(test_count == 10):
		# 	active_users.pop('cirlab',None)
		# 	print("active_users.pop('cirlab',None)")



			# if not list_of_nodes[nodeid]['active'] and nodeid in list_of_nodes_running:
			# 	list_of_nodes_running.remove(nodeid)
			# if list_of_nodes[nodeid]['active'] and nodeid not in list_of_nodes_running:
			# 	list_of_nodes_running.append(nodeid)
			# 	server = Process(target=start_collection_from,args=([nodeid,manager_proxy_nodes_status]))
			# 	server.start()

	## OLD CODES
	# # nodes_status = list_of_nodes
	# while(True):
	# 	# list_of_nodes = {}
	# 	print("1")
	# 	nodes_status_file = open("db_nodes.csv",'r')
	# 	line = nodes_status_file.readline() # header
	# 	line = nodes_status_file.readline()
	# 	print("2")
	# 	while(line!=""):
	# 		line_split = line.split(",")
	# 		print(line_split)
	# 		nodeid = line_split[0]
	# 		list_of_nodes[nodeid] = {}
	# 		list_of_nodes[nodeid]['gateway_ip'] = line_split[1]
	# 		list_of_nodes[nodeid]['gateway_port'] = int(line_split[2])
	# 		list_of_nodes[nodeid]['active'] = int(line_split[3])
	# 		line = nodes_status_file.readline()

	# 	print(list_of_nodes)
	# 	print(list_of_nodes_running)

	# 	for nodeid in list_of_nodes.keys():
	# 		print(nodeid, list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port'])
	# 		if manager_proxy_nodes_status.get(nodeid) != None: # node socket dead and trying to reactivate...
	# 			if manager_proxy_nodes_status[nodeid] == 0 and list_of_nodes[nodeid]['active'] == 1: # replace 0 something like with deactivated and 1 with active
	# 				server = Process(target=start_collection_from,args=([nodeid,manager_proxy_nodes_status]))
	# 				server.start()
	# 				if list_of_nodes[nodeid]['active'] and nodeid not in list_of_nodes_running:
	# 					list_of_nodes_running.append(nodeid)

	# 		manager_proxy_nodes_status[nodeid] = list_of_nodes[nodeid]['active']

	# 		if not list_of_nodes[nodeid]['active'] and nodeid in list_of_nodes_running:
	# 			list_of_nodes_running.remove(nodeid)
	# 		if list_of_nodes[nodeid]['active'] and nodeid not in list_of_nodes_running:
	# 			list_of_nodes_running.append(nodeid)
	# 			server = Process(target=start_collection_from,args=([nodeid,manager_proxy_nodes_status]))
	# 			server.start()
	# 	print("3")
	# 	print(manager_proxy_nodes_status)

	# 	sleep(5)

# def start_collection_from(nodeid, manager_proxy_nodes_status):
def start_collection_from(nodeid, gateway, port, manager_proxy_nodes_status):

	tmp_mote_lock = fasteners.InterProcessLock('/tmp/tmp_mote_lock_' + nodeid)
	x = tmp_mote_lock.acquire(blocking=True)

	logger.info("ATTEMPTING TO CREATE SOCKET to server/node " + str(nodeid) +  "@" + gateway +":"+ str(port))
	sock_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	# sock_node.connect((json_nodes_virt_id_phy_id[nodeid]['gateway'],json_nodes_virt_id_phy_id[nodeid]['port']))
	sock_node.connect((gateway, port))


	sock_aggr_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_aggr_server.connect((server_aggr_ip, server_aggr_port))

	sock_rt_stream_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

	last_dangling_chunk = ""

	count=0
	while True:
		if(manager_proxy_nodes_status[nodeid]):

			#print("PROCESS","manager_proxy_nodes_status['111']",manager_proxy_nodes_status['111'])

			# print("connecting to node", nodeid)
			try:
				data_received = sock_node.recv(4096)
				if not data_received: break
				# data_received = data_received
				data_received = data_received.decode('utf-8','ignore')
				if('\n' in data_received):
					data_received_split = data_received.split('\n')
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
				else:
					last_dangling_chunk = last_dangling_chunk + data_received
			except:
				print(traceback.print_exc())
				print("SOCKET ERR to server/node", nodeid)
				manager_proxy_nodes_status[nodeid]=0
				print("4 except")
				print(manager_proxy_nodes_status)
				# list_of_nodes_running.remove(nodeid)
				sock_aggr_server.close()
				sock_node.close()
				logger.warning("SOCKET ERR to server/node " + str(nodeid))
				tmp_mote_lock.release()
				break
		else:
			break

	print("closing socket to server and node", nodeid)
	logger.warning("CLOSING SOCKET to server/node " + str(nodeid))
	tmp_mote_lock.release()
	# sleep(5)
	# print("5 ERR")
	manager_proxy_nodes_status[nodeid]=0
	print(manager_proxy_nodes_status)
	# if nodeid in list_of_nodes_running:
	# 	list_of_nodes_running.remove(nodeid)
	sock_aggr_server.close()
	sock_node.shutdown(socket.SHUT_RDWR)
	sock_node.close()


# with Manager() as manager:

# 	manager_proxy_nodes_status = manager.dict()

# 	server = Process(target=check_nodes_status_from_db,args=([manager_proxy_nodes_status]))
# 	server.start()


# 	# server.join()

# 	while True:
# 		sleep(5)


