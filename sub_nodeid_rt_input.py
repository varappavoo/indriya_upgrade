#!/usr/bin/python3
import time
import paho.mqtt.client as paho
from multiprocessing import Process
import socket
import json
from secrets import *

# from active_jobs import *

import logging
import logging.config


logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('rt_input')

active_users_copy = {}
broker="ocean.comp.nus.edu.sg"
with open('nodes_virt_id_phy_id.json') as json_data:
	json_nodes_virt_id_phy_id = json.load(json_data)

# broker="iot.eclipse.org"
#define callback

# list_of_nodes={}
# nodes_status_file = open("db_nodes.csv",'r')
# line = nodes_status_file.readline() # header
# line = nodes_status_file.readline()
# while(line!=""):
# 	line_split = line.split(",")
# 	nodeid = line_split[0]
# 	list_of_nodes[nodeid] = {}
# 	list_of_nodes[nodeid]['gateway_ip'] = line_split[1]
# 	list_of_nodes[nodeid]['gateway_port'] = int(line_split[2])
# 	list_of_nodes[nodeid]['active'] = int(line_split[3])
# 	line = nodes_status_file.readline()


def on_message(client, userdata, message):
	global active_users_copy
	print("received message = ", str(message.topic) + " - " + str(message.payload.decode("utf-8")))
	user =  str(message.topic).split("/")[0]
	nodeid = str(message.topic).split("/")[2]
	value = str(message.payload.decode("utf-8"))
	print(active_users_copy)
	logger.info(str(active_users_copy))
	print("nodeid:",nodeid,"value:",value)
	if nodeid in active_users_copy[user]:
		print("user", user, "booked",nodeid)
		logger.info("user " + user + " booked " + nodeid + "; sending: " +  value)
		# if(list_of_nodes.get(nodeid) != None):
		# 	if(list_of_nodes[nodeid]['active']):
		server = Process(target=send_data_to_usb,args=([nodeid,value]))
		server.start()
	else:
		print("user", user, "did not book",nodeid)
		logger.warn("user " + user + " did not book " + nodeid + "; sending: " +  value)


def send_data_to_usb(nodeid,value):
	sock_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock_node.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
	sock_node.connect((json_nodes_virt_id_phy_id[nodeid]['gateway'], json_nodes_virt_id_phy_id[nodeid]['port']))
	sock_node.send(str.encode(value,'utf-8') + str.encode("\n"))
	sock_node.close()


def accept_rt_input(active_users):
	global active_users_copy
	active_users_copy = active_users
	logger.info("starting real time input from users")
	client= paho.Client("client-indriya") 
	client.on_message=on_message
	#client.username_pw_set("indriya", password="indriya123")
	client.username_pw_set(mqtt_user, password=mqtt_password)
	print("connecting to broker ",broker)
	client.connect(broker)
	client.loop_start() 
	print("subscribing ")
	client.subscribe("+/push/#") # + wildcard for single level wildcard
	client.subscribe("+/pull/#") # + wildcard for single level wildcard
	while(1):
		time.sleep(10)
