#!/usr/bin/python3
# from flask import Flask
from flask import Flask, request
import json
import run_jobs
from get_data_from_nodes import *
from aggregator import *
# import get_data_from_nodes

app = Flask(__name__)

# from active_users import *

# curl -H "Content-Type: application/json" -X POST -d @jobs_waiting.json http://localhost:5000/new_job
@app.route("/new_job", methods=['POST'])
def new_job():
	json_data = request.json
	for key in json_data:
		print(key,json_data[key])
	# disconnect before burning...
	# burn_results = run_jobs.schedule_job(json_data)
	# print(burn_results)
	return "JOB:\n" + str(json_data)

@app.route("/active_users", methods=['POST'])
def users():
	# global active_users
	# json_data = request.json
	# print()
	return str(active_users)

# curl -H "Content-Type: application/json" -X POST -d '{"cirlab":""}' http://localhost:5000/test
@app.route("/test", methods=['POST'])
def test():
	json_data = request.json
	for key in json_data:
		active_users.pop(key)
	return str(active_users)

if __name__ == '__main__':
	###############################################################################################################
	#### get_data_from_nodes
	###############################################################################################################
	with Manager() as manager:


		manager_proxy_nodes_status = manager.dict()
		active_users = manager.dict()

		active_users['cirlab']=['255','235','7041']
		active_users['alice']=['211']
		active_users['bob']=['205']
		active_users['malory']=['555']

		aggregator_server = Process(target=listen,args=([active_users]))
		aggregator_server.start()
		sleep(5)

		get_data_from_nodes_server = Process(target=check_nodes_status_from_db,args=([manager_proxy_nodes_status,active_users]))
		get_data_from_nodes_server.start()



		app_server = Process(target=app.run,args=())
		app_server.start()

		get_data_from_nodes_server.join()

		# server.join()

		# while True:
		# 	sleep(5)
	###############################################################################################################
	#### get_data_from_nodes
	###############################################################################################################
	# print("----------------------------------------------------------------")
	# app.run(debug=True, port=5000)	