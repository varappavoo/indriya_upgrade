#!/usr/bin/python3
import socket
from threading import Thread
# from socketserver import ThreadingMixIn

from influxdb import InfluxDBClient
from random import randint
import sys
import multiprocessing
import traceback
import json

#from logging.handlers import RotatingFileHandler
import logging
import logging.config


logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('aggregator')

from config import *

#user = 'root'
#password = 'root'

# nodeid = 333

from time import time,sleep
from datetime import datetime

import paho.mqtt.client as mqtt

# NEED TO WRITE A THREAD THAT CONTINUOULY POLLS MYSQLDB AND UPDATE THE active_jobs DICTIONARY
from active_jobs import *
#active_jobs={}
#active_jobs['1abc']=['255','235','7041']
#active_jobs['2eee']=['211']
#active_jobs['44dd']=['205']
#active_jobs['55ee']=['555']

json_body = []
count=0
client = InfluxDBClient(host, port, dbuser, dbuser_password, dbname)
start = time()
tmp_time = start

mqtt_broker="localhost"
port=1883
mqtt_client = mqtt.Client(client_id="indriya_server")
mqtt_qos = 0 #QoS 0 at most once (fire and forget), 1 at least once (broker acknowledges),   2 exactly once hence most expensive

def on_publish(client,userdata,result):
	pass

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT server: %s" % rc)
    while rc != 0:
        sleep(1)
        print("Reconnecting...")
        rc = client.reconnect()


mqtt_client.on_publish = on_publish                       
mqtt_client.username_pw_set("indriya", password="indriya123")
mqtt_client.connect(mqtt_broker,port) 
mqtt_client.loop_start()

def update_jobs():
	# check db/file for jobs and respective nodes involved
	pass

def execute_request(start,json_body):
	result =  client.write_points(json_body)#,time_precision='u')   

def savetodb_batching(json_data):
	global json_body, count, start, tmp_time, active_jobs, mqtt_client
	# current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

	# sleep(0.00001)
	json_body.append({
		"measurement": table,
		"time": json_data['time'],#current_time,
		# "tags": {"nodeid": data_split[0]},
		"tags": {"nodeid": json_data['nodeid']},
		# "fields": {"data": '1234567890123456789012345678901234567890_' + str(value)}
		# "fields": {"ts": time(),"data": '123456789012345678901234567890_' + str(value)}
		# "fields": {"nodeid": data_split[0],"data": data_split[1]}
		# "fields": {"value": ",".join(data_split[1:])}
		"fields": {"value": json_data['value']}
	})
	count=count+1
	# except:
	# 	print("invalid nodeid",data_split[0])
	#     # print(traceback.print_exc())
	for key in active_jobs.keys():
		#print("1",json_data['nodeid'],active_jobs[key])
		if (json_data['nodeid'] in active_jobs[key]):
			# print("2",key,json_data['nodeid'],active_jobs[key])
			print("mqtt_client.publish",key, json.dumps(json_data), mqtt_qos)
			print(mqtt_client.publish(key, json.dumps(json_data), mqtt_qos))

	now = time()
	if(now - tmp_time >= 10 or count==db_batch_size):
		# print(i)
		server = multiprocessing.Process(target=execute_request,args=([start,json_body]))
		server.start()
		json_body = []
		tmp_time = now
		count=0

def dispatcher(json_data):
	# assign ports to active jobs and forward the data...
	pass

# client = InfluxDBClient(host, port, dbuser, dbuser_password, dbname)
# start = time()
# tmp_time = start

# def execute_request(start,json_body):
# 	result =  client.write_points(json_body)#,time_precision='u')   
	# print(result)
	# print(time()-start)


#####################################################################################
##
## Multithreaded Python server : TCP Server Socket Thread Pool
## adapted client thread and server code from http://www.techbeamers.com/python-tutorial-write-multithreaded-python-server/
##
#####################################################################################
class ClientThread(Thread):

	def __init__(self,ip,port,sock):
		Thread.__init__(self)
		self.ip = ip
		self.port = port
		self.sock = sock
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
		print("[+] New server socket thread started for " + ip + ":" + str(port))
		logger.info("new server socket thread started for " + ip + ":" + str(port))

	def run(self):
		tmp_time = time()
		json_body = []
		json_data = {}
		last_dangling_chunk = ""
		count=0
		while True :
			# test()
			try:
				data_received = self.sock.recv(4096)
				if not data_received: break
				# print(data_received.decode('utf-8').split('\n'))
				data_received_split = data_received.decode('utf-8').split('\n')
				# for json_chunk in data_received_split:
				for i in range(len(data_received_split) - 1): # last chunk is likely to be incomplete
					# data = json.load(data_received)
					# print(data_received.decode('utf-8'))
					# print(json_chunk)
					if i == 0: 
						json_data = json.loads(last_dangling_chunk + data_received_split[0])
					else:
						json_data = json.loads(data_received_split[i])

					current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
					json_data['time']=current_time
					print(json_data)

					savetodb_batching(json_data)

				last_dangling_chunk = data_received_split[-1]
			except:
				# print(data_received.decode('utf-8'))
				print(traceback.print_exc())


 
# Multithreaded Python server : TCP Server Socket Program Stub
# TCP_IP = '0.0.0.0'
# TCP_PORT = server_aggr_port
print("listening on port",server_aggr_port)
# BUFFER_SIZE = 1024  # Usually 1024, but we need quick response
 
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpServer.bind(("0.0.0.0", server_aggr_port))
threads = []
while True:
	tcpServer.listen(100)
	print("Multithreaded Python aggregator server : Waiting for connections from TCP clients...")
	logger.info('aggregator started')
	(client_sock, (ip,port)) = tcpServer.accept()
	newthread = ClientThread(ip,port,client_sock)
	newthread.start()
	threads.append(newthread)

# for t in threads:
#     t.join()
