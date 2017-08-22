#!/usr/bin/python3
from secrets import *
import socket
from threading import Thread
# from socketserver import ThreadingMixIn

from influxdb import InfluxDBClient
from random import randint
import sys
import multiprocessing
import traceback
import json



#user = 'root'
#password = 'root'
dbname = 'experiment'
dbuser = admin
dbuser_password = admin_password
table = 'test'
host='localhost'
port=8086
nodeid = 333

from time import time,sleep
from datetime import datetime


client = InfluxDBClient(host, port, dbuser, dbuser_password, dbname)
start = time()
tmp_time = start

def execute_request(start,json_body):
	result =  client.write_points(json_body)#,time_precision='u')   
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

	def run(self):
		tmp_time = time()
		json_body = []
		json_data = {}
		last_dangling_chunk = ""
		count=0
		while True :
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

					print(json_data)
					# data_received = data_received[2:-3]
					# data = str(self.socket.recv(2048))

					
					# data_loaded = json.loads(data_received)
					# print(data)
					# for data in data_received.split("\\n"):
						# print(data)
					# try:
					#     # data = data.strip()[2:-3] # b'333,12345678901234567890\n'
					#     # data = data.strip()[2:] # b'333,12345678901234567890\n'
						
					#     # print(data)
					#     data_split = data.split(",")
					#     # print("Server received data:", data)
					#     # MESSAGE = input("Multithreaded Python server : Enter Response from Server/Enter exit:")
					#     # if MESSAGE == 'exit':
					#     #     break
					#     # conn.send(MESSAGE)  # echo
						# try:
							
					# nodeid = 
					current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

					# sleep(0.00001)
					json_body.append({
						"measurement": table,
						"time": current_time,
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

					now = time()
					if(now - tmp_time >= 10 or count%5000==0):
						# print(i)
						server = multiprocessing.Process(target=execute_request,args=([start,json_body]))
						server.start()
						json_body = []
						tmp_time = now
						count=0
					# except:
					#     print(traceback.print_exc())

				last_dangling_chunk = data_received_split[-1]
			except:
				# print(data_received.decode('utf-8'))
				print(traceback.print_exc())


 
# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 9000
# BUFFER_SIZE = 1024  # Usually 1024, but we need quick response
 
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []
while True:
	tcpServer.listen(100)
	print("Multithreaded Python server : Waiting for connections from TCP clients...")
	(client_sock, (ip,port)) = tcpServer.accept()
	newthread = ClientThread(ip,port,client_sock)
	newthread.start()
	threads.append(newthread)

# for t in threads:
#     t.join()
