#!/usr/bin/python3
import time
import paho.mqtt.client as paho
from multiprocessing import Process
import socket

broker="ocean.comp.nus.edu.sg"
# broker="iot.eclipse.org"
#define callback

list_of_nodes={}
nodes_status_file = open("db_nodes.csv",'r')
line = nodes_status_file.readline() # header
line = nodes_status_file.readline()
while(line!=""):
	line_split = line.split(",")
	nodeid = line_split[0]
	list_of_nodes[nodeid] = {}
	list_of_nodes[nodeid]['gateway_ip'] = line_split[1]
	list_of_nodes[nodeid]['gateway_port'] = int(line_split[2])
	list_of_nodes[nodeid]['active'] = int(line_split[3])
	line = nodes_status_file.readline()


def on_message(client, userdata, message):
	# time.sleep(1)
	print("received message = ", str(message.topic) + " - " + str(message.payload.decode("utf-8")))
	nodeid = str(message.topic).split("/")[1]
	value = str(message.payload.decode("utf-8"))
	print("nodeid:",nodeid,"value:",value)
	if(list_of_nodes.get(nodeid) != None):
		if(list_of_nodes[nodeid]['active']):
			server = Process(target=send_data_to_usb,args=([nodeid,value]))
			server.start()

def send_data_to_usb(nodeid,value):
	sock_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_node.connect((list_of_nodes[nodeid]['gateway_ip'], list_of_nodes[nodeid]['gateway_port']))
	sock_node.send(str.encode(value,'utf-8') + str.encode("\n"))
	sock_node.close()

	# sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	# sock_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	# sock_server.connect((server_ip, server_savetodb_port))

	# sock_aggr_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	# sock_aggr_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	# sock_aggr_server.connect((server_aggr_ip, server_aggr_port))

	# sock_rt_stream_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	
	# TCP_IP = '0.0.0.0'
	# TCP_PORT = 9000 + int(nodeid)
	# sock_dup = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock_dup.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# sock_dup.bind((TCP_IP, TCP_PORT))
	# sock_dup.listen(100)
	# (client_sock_dub, (ip,port)) = tcpServer.accept()

	# last_dangling_chunk = ""

	# count=0
	# while True:
	# 	if(manager_proxy_nodes_status[nodeid]):

	# 		#print("PROCESS","manager_proxy_nodes_status['111']",manager_proxy_nodes_status['111'])

	# 		# print("connecting to node", nodeid)
	# 		try:
	# 			data_received = sock_node.recv(4096)
	# 			if not data_received: break
	# 			# data_received = data_received

	# 			data_received_split = data_received.decode('utf-8','ignore').split('\n')
	# 			# data_received_split = data_received.split('\n')
	# 			for i in range(len(data_received_split) - 1): # last chunk is likely to be incomplete
	# 				json_data ={}#'{"nodeid":' + nodeid', "value": "123456789012345678901234567890123456789012345678901234567890abcdxyz"}'
	# 				count = count + 1
	# 				json_data['nodeid'] = nodeid
	# 				if i == 0: 
	# 					json_data['value'] = last_dangling_chunk + data_received_split[0]
	# 				else:
	# 					json_data['value'] = data_received_split[i]

	# 				data_string = json.dumps(json_data)
	# 				print(data_string)
	# 				# sock_server.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
	# 				sock_aggr_server.send(str.encode(data_string,'utf-8') + str.encode("\n")) # encode to from str to byte
	# 				sock_rt_stream_udp.sendto(str.encode(data_string,'utf-8') + str.encode("\n"), ('localhost', UDP_PORT+int(nodeid)))
	# 				print(UDP_PORT+int(nodeid))
	# 			last_dangling_chunk = data_received_split[-1]
	# 		except:
	# 			print(traceback.print_exc())
	# 	else:
	# 		break


client= paho.Client("client-001") #create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
######Bind function to callback
client.on_message=on_message
#####
print("connecting to broker ",broker)
client.connect(broker)#connect
client.loop_start() #start loop to process received messages
print("subscribing ")
client.subscribe("pull/#")#subscribe
time.sleep(1)
print("testing by pulishing...")
client.publish("pull/235","on")#publish
while(1):
	time.sleep(1)
# client.disconnect() #disconnect
# client.loop_stop() #stop loop