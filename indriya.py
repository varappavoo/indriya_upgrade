#!/usr/bin/python3
# from flask import Flask
from flask import Flask, request
import json
import run_jobs
from get_data_from_nodes import *
from aggregator import *
from sub_nodeid_rt_input import *
from zip_job_data import *

import sched
from _thread import start_new_thread
from time import time,sleep

# import get_data_from_nodes
GAP_BEFORE_STARTING_NEW_JOB = 5
import logging

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('indriya_main')

app = Flask(__name__)

first_run=1


def check_scheduler():
	# global scheduler
	while(True):
		print("check_scheduler",scheduler.queue)
		if(len(scheduler.queue) > 0):
			scheduler.run(blocking=False)
		sleep(1)



def schedule_job(json_data):
	# logger.info("processing job for result_id..." + str(json_data['result_id']))
	start_new_thread(process_job,(json_data,))
	# process_job(json_data)

def finish_job(json_data):
	# logger.info("finishing job with result_id..." + str(json_data['result_id']))
	# start_new_thread(compile_compress_data_for_job(json_data))
	start_new_thread(compile_compress_data_for_job,(json_data,))

def compile_compress_data_for_job(json_data):
	logger.info("compiling and compressing data for result: " + str(json_data['result_id']))
	zip_data_for_result(json_data)
	# mote_list = []
	# for i in range(len(json_data['job_config'])):
	# 	 mote_list = mote_list + json_data['job_config'][i]['mote_list']
	# deactive_motes(mote_list)


# curl -H "Content-Type: application/json" -X POST -d @jobs_waiting.json http://localhost:5000/new_job
def deactive_motes(mote_list):
	print('deactive_motes(mote_list)')
	logger.info("deactivating motes " + str(mote_list))
	print(active_users)
	print(mote_list)
	for user in active_users.keys():
		temp_list=[]
		for nodeid in active_users[user]:
			print("nodeid",nodeid)
			if nodeid not in mote_list:
				temp_list.append(nodeid)
				# print("removing",nodeid)
				# active_users[user].remove(nodeid)
				# print("active_users[" + user + "]",active_users[user])
		if len(temp_list) == 0:
			active_users.pop(user,None)
		else:
			active_users[user]=temp_list
	print(active_users)
	sleep(5) # takes some time as process polls... to check active motes from active users lists

def burn_motes(json_data):
	print('burn_motes(json_data)')
	burn_results = run_jobs.schedule_job(json_data)
	print(burn_results)
	return burn_results

def update_active_users(user,mote_list):
	print('update_active_users(user,mote_list)')
	if(active_users.get(user) == None):
		active_users[user]=[]
	active_users[user] = active_users[user] + mote_list
	print(active_users)


def process_job(json_data):
	# print('process_job(json_data)')
	logger.info("processing job submitted by " + str(json_data['user']) + " result_id " + str(json_data['result_id']))
	sleep(GAP_BEFORE_STARTING_NEW_JOB)
	mote_list = []
	for i in range(len(json_data['job_config'])):
		 mote_list = mote_list + json_data['job_config'][i]['mote_list']
	deactive_motes(mote_list)
	burn_results = burn_motes(json_data)
	save_burn_log(json_data, burn_results)
	update_active_users(json_data['user'],mote_list)
	# print('#############################################################################################')

def add_job_to_job_queue_and_scheduler(json_data):
	global first_run
	if(first_run):
		start_new_thread(check_scheduler,())
		first_run = 0
	try:
		jobs_queue[json_data['result_id']]={}
		jobs_queue[json_data['result_id']]['json_data']=json_data
		e_start = scheduler.enterabs(int(json_data['time']['from']), 1, schedule_job, (json_data,))
		e_finish = scheduler.enterabs(int(json_data['time']['to']), 1, finish_job, (json_data,))

		# e_start = scheduler.enter(int(json_data['time']['from']), 1, schedule_job, (json_data,))
		# e_finish = scheduler.enter(int(json_data['time']['to']), 1, finish_job, (json_data,))
		
		jobs_queue[json_data['result_id']]['job_schedule_event'] = e_start
		jobs_queue[json_data['result_id']]['job_finish_event'] = e_finish
		logger.info("new job submitted by " + str(json_data['user']) + " added to job queue")
		return "1"
	except:
		return "0"


def cancel_job_from_queue(json_data):
	print("before cancel job",scheduler.queue)
	if(jobs_queue.get(json_data['result_id']) != None):
		scheduler.cancel(jobs_queue[json_data['result_id']]['job_schedule_event'])
		scheduler.cancel(jobs_queue[json_data['result_id']]['job_finish_event'])
		print("after cancel job",scheduler.queue)
		logger.info("Job, with result_id " +  json_data['result_id'] + ", was cancelled")
		return "1"
	else:
		logger.warn("trying to cancel job, with result_id " +  json_data['result_id'] + ", that does not exist")
		return "0"

@app.route("/cancel_job", methods=['POST'])
def cancel_job():
	json_data = request.json
	logger.info("REQUEST: job with resultid " + json_data['result_id'] + " cancelled by " + str(json_data['user']) + "@" + str(time()) + " to be running from " + json_data['time']['from'] + " to " + json_data['time']['to'])
	result = cancel_job_from_queue(json_data)
	return result + "/n"

@app.route("/new_job", methods=['POST'])
def new_job():
	json_data = request.json
	print(json_data)
	logger.info("REQUEST: new job with resultid" + json_data['result_id'] + " submitted by " + str(json_data['user']) + "@" + str(time()) + " to be running from " + json_data['time']['from'] + " to " + json_data['time']['to'])
	result = add_job_to_job_queue_and_scheduler(json_data)
	return result + "/n"

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
	jobs_queue = {}
	scheduler = sched.scheduler(time, sleep)
	
	###############################################################################################################
	#### get_data_from_nodes
	###############################################################################################################
	with Manager() as manager:


		manager_proxy_nodes_status = manager.dict()
		active_users = manager.dict()
		# scheduler_dict = manager.dict()
		# scheduler_dict['scheduler'] = scheduler

		aggregator_server = Process(target=listen,args=([active_users]))
		aggregator_server.start()
		sleep(2)

		get_data_from_nodes_server = Process(target=check_nodes_status_from_db,args=([manager_proxy_nodes_status,active_users]))
		get_data_from_nodes_server.start()

		sub_nodeid_rt_input_server = Process(target=accept_rt_input,args=([active_users]))
		sub_nodeid_rt_input_server.start()

		app_server = Process(target=app.run,args=())
		app_server.start()

		# scheduler_server = Process(target=run_scheduler,args=([scheduler_dict]))
		# scheduler_server.start()

		get_data_from_nodes_server.join()

