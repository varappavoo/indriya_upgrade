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



client= paho.Client("client-001") 
client.on_message=on_message
print("connecting to broker ",broker)
client.connect(broker)
client.loop_start() 
print("subscribing ")
client.subscribe("pull/#")
while(1):
	time.sleep(10)
