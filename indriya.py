#!/usr/bin/python3
# from flask import Flask
from flask import Flask, request
import json
import run_jobs
from get_data_from_nodes import *
from aggregator import *
from sub_nodeid_rt_input import *
from zip_job_data import *
import fasteners
from mqtt_user import *

import sched
from _thread import start_new_thread
from time import time,sleep

import threading
active_users_lock = threading.Lock()
job_queue_lock = threading.Lock()
running_jobs_lock = threading.Lock()

# import get_data_from_nodes
GAP_BEFORE_STARTING_NEW_JOB = 5
GAP_AFTER_DEACTIVATING_MOTES = 2
JOB_MIN_RUNNING_TIME = 60
import logging

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('indriya_main')

app = Flask(__name__)

first_run=1
running_jobs = {}
running_jobs['active'] = []

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
	global jobs_queue, running_jobs
	result_id = str(json_data['result_id'])
	logger.info("compiling and compressing data for result: " + result_id)
	zip_data_for_result(json_data)
	mote_list = []
	for i in range(len(json_data['job_config'])):
		 mote_list = mote_list + json_data['job_config'][i]['mote_list']
	deactive_motes(mote_list)

	if(result_id in running_jobs['active']):
		running_jobs_lock.acquire()
		# logger.info("running_jobs B" + str(running_jobs) + " " + result_id)
		running_jobs['active'].remove(result_id)
		# logger.info("running_jobs A" + str(running_jobs) + " " + result_id)
		running_jobs_lock.release()

	job_queue_lock.acquire()
	if(jobs_queue.get(json_data['result_id']) != None):
		jobs_queue.pop(json_data['result_id'],None)
	job_queue_lock.release()




# curl -H "Content-Type: application/json" -X POST -d @jobs_waiting.json http://localhost:5000/new_job
def deactive_motes(mote_list):
	print("trying to deactivate motes...")
	active_users_lock.acquire()
	print('deactive_motes(mote_list)')
	mote_list.sort()
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
	active_users_lock.release()
	sleep(GAP_AFTER_DEACTIVATING_MOTES) # takes some time as process polls... to check active motes from active users lists

def update_active_users(user,mote_list):
	active_users_lock.acquire()
	print('update_active_users(user,mote_list)')
	if(active_users.get(user) == None):
		active_users[user]=[]
	active_users[user] = active_users[user] + mote_list
	print(active_users)
	active_users_lock.release()

def burn_motes(json_data):
	print('burn_motes(json_data)')
	burn_results = run_jobs.schedule_job(json_data)
	print(burn_results)
	return burn_results

def process_job(json_data):
	# print('process_job(json_data)')
	global running_jobs
	result_id = json_data['result_id']
	logger.info("processing job submitted by " + str(json_data['user']) + " result_id " + str(result_id))
	# sleep(GAP_BEFORE_STARTING_NEW_JOB)
	mote_list = []
	for i in range(len(json_data['job_config'])):
		 mote_list = mote_list + json_data['job_config'][i]['mote_list']
	deactive_motes(mote_list)

	burn_process = Process(target=burn_motes,args=([json_data]))
	burn_process.start()
	# burn_results = burn_motes(json_data)
	# logger.info(result_id + " " +str(burn_results))
	# save_burn_log(json_data, burn_results)
	tmp_job_lock = fasteners.InterProcessLock('/tmp/tmp_job_lock_' + result_id)
	tmp_job_lock.acquire(blocking=True)
	tmp_job_lock.release() # just make sure that the burning is done :)

	mote_list_burnt = check_successful_burn(json_data)
	if(len(mote_list_burnt) > 0):
		logger.warn(str(len(mote_list_burnt)) + '/' + str(len(mote_list)) + ' motes are succussfully burn for job ' + result_id)
		update_active_users(json_data['user'],mote_list_burnt)
		running_jobs_lock.acquire()
		# logger.info("running_jobs B" + str(running_jobs) + " " + result_id)
		running_jobs['active'] = running_jobs['active'] + [result_id]
		# logger.info("running_jobs A" + str(running_jobs))
		running_jobs_lock.release()
	else:
		logger.warn('job ' + result_id + ' is cancelled as all motes are unsuccessful burnt')
		scheduler.cancel(jobs_queue[result_id]['job_finish_event'])
		compile_compress_data_for_job(json_data)


	# print('#############################################################################################')

def check_successful_burn(json_data):
	print("check success",json_data)
	motes_successfully_burnt = []
	burn_results =read_burn_log(json_data)
	for key in burn_results["job_config"].keys():
		moteids = burn_results["job_config"][key].keys()
		for moteid in moteids:
			if(burn_results["job_config"][key][moteid]['burn']=='1'):
				motes_successfully_burnt.append(moteid)
				print(moteid)
	return motes_successfully_burnt

def add_job_to_job_queue_and_scheduler(json_data):
	global first_run, jobs_queue
	if(first_run):
		start_new_thread(check_scheduler,())
		first_run = 0
	try:
		job_queue_lock.acquire()
		jobs_queue[json_data['result_id']]={}
		jobs_queue[json_data['result_id']]['json_data']=json_data
		e_start = scheduler.enterabs(int(json_data['time']['from']) + GAP_BEFORE_STARTING_NEW_JOB, 1, schedule_job, (json_data,))
		e_finish = scheduler.enterabs(int(json_data['time']['to']) - GAP_BEFORE_STARTING_NEW_JOB, 1, finish_job, (json_data,))

		# e_start = scheduler.enter(int(json_data['time']['from']), 1, schedule_job, (json_data,))
		# e_finish = scheduler.enter(int(json_data['time']['to']), 1, finish_job, (json_data,))
		
		jobs_queue[json_data['result_id']]['job_schedule_event'] = e_start
		jobs_queue[json_data['result_id']]['job_finish_event'] = e_finish
		logger.info("new job submitted by " + str(json_data['user']) + " added to job queue")
		job_queue_lock.release()
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "1"
	except:
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "0"


def cancel_job_from_queue(json_data):
	global jobs_queue, running_jobs
	print("before cancel job",scheduler.queue)
	#lock
	result_id = json_data['result_id']
	job_queue_lock.acquire()
	if(jobs_queue.get(result_id) != None):
		now = time()
		job_time_from = int(jobs_queue[result_id]['json_data']['time']['from'])
		job_time_to = int(jobs_queue[result_id]['json_data']['time']['to'])
		# print("--------------------------------------------------------------------------------------")
		# print(jobs_queue[result_id]['json_data']['time']['from'], str(int(now)))
		# print("--------------------------------------------------------------------------------------")
		if(job_time_from > int(now)):
			scheduler.cancel(jobs_queue[result_id]['job_schedule_event'])
			logger.info("job schedule event, with result_id " +  result_id + ", was cancelled")
		if(job_time_to > int(now) - GAP_BEFORE_STARTING_NEW_JOB):
			scheduler.cancel(jobs_queue[result_id]['job_finish_event'])
			logger.info("job compiling/zipping event, with result_id " +  result_id + ", was cancelled")
		# print("after cancel job",scheduler.queue)

		if(job_time_from < now < job_time_to):
			mote_list = []
			for i in range(len(jobs_queue[result_id]['json_data']['job_config'])):
				 mote_list = mote_list + jobs_queue[result_id]['json_data']['job_config'][i]['mote_list']
			deactive_motes(mote_list)
			
			if(result_id in running_jobs['active']):
				running_jobs_lock.acquire()
				running_jobs['active'].remove(result_id)
				running_jobs_lock.release()
		
		logger.info("Job, with result_id " +  result_id + ", is cancelled")

		jobs_queue.pop(result_id,None)
		job_queue_lock.release()
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "1"
	else:
		logger.warn("trying to cancel job, with result_id " +  result_id + ", that does not exist")
		job_queue_lock.release()
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "0"
	

@app.route("/cancel_job", methods=['POST'])
def cancel_job():
	json_data = request.json
	logger.info("REQUEST: job with resultid " + json_data['result_id'] + " is called for cancelation")# + str(json_data['user']) + "@" + str(time()) + " to be running from " + json_data['time']['from'] + " to " + json_data['time']['to'])
	result = cancel_job_from_queue(json_data)
	response={}
	response['result_id']=json_data['result_id']
	response['action']='cancel_job'
	response['result']=result
	return str(response)

@app.route("/active_users", methods=['GET','POST'])
def active_users():
	return str(active_users)

@app.route("/active_jobs", methods=['GET','POST'])
def active_jobs():
	return str(running_jobs)

@app.route("/get_burn_results", methods=['GET','POST'])
def get_burn_results():
	json_data = request.json
	data = read_burn_log(json_data)
	return str(data)

@app.route("/new_job", methods=['GET','POST'])
def new_job():
	print(request)
	json_data = request.json
	print(json_data)
	logger.info("REQUEST: new job " + json_data['result_id'] + " submitted by " + str(json_data['user']) + " @ " + str(time()) + ", to run from " + json_data['time']['from'] + " to " + json_data['time']['to'])

	mote_list = []
	for i in range(len(json_data['job_config'])):
		 mote_list = mote_list + json_data['job_config'][i]['mote_list']
	mote_list.sort()
	logger.info("REQUEST: new job with resultid "  + json_data['result_id'] + " with " + str(mote_list))

	response={}
	response['result_id']=json_data['result_id']
	response['action']='new_job'
	now = time()
	if((int(json_data['time']['to']) - int(json_data['time']['from'])) > JOB_MIN_RUNNING_TIME and int(json_data['time']['to']) < now + JOB_MIN_RUNNING_TIME): # min running time
		logger.info("REQUEST: new job with resultid "  + json_data['result_id'] + " is too short for schedule")
		response['result']="0"
	else:
		result = add_job_to_job_queue_and_scheduler(json_data)
		response['result']=result
	return str(response)

@app.route("/new_mqtt_user", methods=['POST'])
def new_mqtt_user():
	json_data = request.json
	user = json_data['user']
	logger.info("REQUEST: new mqtt user," + user)
	password = add_new_mqtt_user(user)
	mqtt_user = {}
	mqtt_user['user'] = user
	mqtt_user['action'] = 'new_mqtt_user'
	if password != None:
		mqtt_user['password'] = password
		mqtt_user['result'] = '1'
	else:
		mqtt_user['result'] = '0'
	return str(mqtt_user)


#@app.route("/active_users", methods=['POST'])
#def users():
#	password = add_new_mqtt_user()
#	# global active_users
#	# json_data = request.json
#	# print()
#	return password + "/n"

# curl -H "Content-Type: application/json" -X POST -d '{"cirlab":""}' http://localhost:5000/test
# @app.route("/test", methods=['POST'])
# def test():
# 	json_data = request.json
# 	for key in json_data:
# 		active_users.pop(key)
# 	return str(active_users)

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

