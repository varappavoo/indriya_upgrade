#!/usr/bin/python3
# from flask import Flask
from termcolor import colored
import random
import pickle

from flask import Flask, request
import json
import run_jobs
from get_data_from_nodes import *
from aggregator import *
from sub_nodeid_rt_input import *
from zip_job_data import *
import fasteners
from mqtt_user import *
from run_config import *

from filelock import FileLock

import sched
from _thread import start_new_thread
from time import time,sleep

from copy import deepcopy

import threading
active_users_lock = threading.Lock()
job_queue_lock = threading.Lock()
running_jobs_lock = threading.Lock()

cancel_jobs_lock = threading.Lock()

# import get_data_from_nodes
# GAP_BEFORE_STARTING_NEW_JOB = 90
# GAP_BEFORE_STARTING_NEW_JOB = 10
TIME_TO_EXECUTE_A_JOB = 120
GAP_AFTER_DEACTIVATING_MOTES = 2
JOB_MIN_RUNNING_TIME = 60

GAP_TO_START_CLEANING_WHEN_CANCELLING_DURING_RUNNING = 10
GAP_TO_START_CLEANING_AFTER_FINISHING_JOB = 5
PROCESS_JOB_LOCK_TIMEOUT = 60
PROCESS_JOB_LOCK_POLL_INTERVAL = 1

import logging

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('indriya_main')

app = Flask(__name__)

telosb_maintenance_binary_filename = "welcome.sky"
cc2650_maintenance_binary_filename = "welcome.elf"

first_run=1
running_jobs = {}
running_jobs['active'] = []
hibernate = 1
perform_maintenance_after_job = 0
if perform_maintenance_after_job:
	GAP_BEFORE_STARTING_NEW_JOB = 90
else:
	GAP_BEFORE_STARTING_NEW_JOB = 1

def check_scheduler():
	global scheduler
	while(True):
		print("check_scheduler",scheduler.queue)
		for event in scheduler.queue:
			print(event[0], (event[3][0])['result_id'] , (event[3][0])['job_config'][0]['mote_list'], event[2],)
		# if(len(scheduler.queue) > 0):
		try:
			scheduler.run(blocking=False)
		except:
			print("check_scheduler exception")
		sleep(60)



def schedule_job(json_data):
	# logger.info("processing job for result_id..." + str(json_data['result_id']))
	start_new_thread(process_job,(json_data,))
	# process_job(json_data)

def finish_job(json_data,maintenance_job=False): # Maintenance True means the finish_job is a maintenance once ;), if it's not, then schedule the maintenance
	# logger.info("finishing job with result_id..." + str(json_data['result_id']))
	# start_new_thread(compile_compress_data_for_job(json_data))
	start_new_thread(compile_compress_data_for_job,(json_data,))
	if perform_maintenance_after_job and not maintenance_job:
		rnd = random.random()
		decimal_place = 10000
		rnd_a_dp = (round(rnd * decimal_place))/decimal_place
		scheduler.enterabs(int(time()) + GAP_TO_START_CLEANING_AFTER_FINISHING_JOB + rnd_a_dp, 1, maintenance_after_finishing_job, (json_data,))

		# sleep(1)
		# #start_new_thread(maintenance_after_finishing_job, (json_data,))
		# maintenance_after_finishing_job(json_data)
		# sleep(1)

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

	pickle.dump( jobs_queue, open( "jobs_queue.p", "wb" ) )
	pickle.dump( scheduler, open( "scheduler.p", "wb" ) )

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
	
	for nodeid in mote_list:
		if active_motes.get(nodeid) != None:
			active_motes.pop(nodeid)

	active_users_lock.release()
	sleep(GAP_AFTER_DEACTIVATING_MOTES) # takes some time as process polls... to check active motes from active users lists

def update_active_users(user,mote_list):
	active_users_lock.acquire()
	print('update_active_users(user,mote_list)')
	if(active_users.get(user) == None):
		active_users[user]=[]
	active_users[user] = active_users[user] + mote_list
	print(active_users)

	for nodeid in mote_list:
		active_motes[nodeid] = user

	active_users_lock.release()

def burn_motes(json_data):
	print('burn_motes(json_data)')
	burn_results = run_jobs.schedule_job(json_data)
	print(burn_results)
	return burn_results

def maintenance_after_finishing_job(json_data):
	try:
		logger.info("performing maintenance after finishing job")
		#json_data_copy = {}
		#json_data_copy = deepcopy(json_data)
		json_data_copy = dict(json_data)
		
		result_id = json_data_copy['result_id']
		
		json_data_copy['result_id'] = json_data['result_id'] + '_maintenance'
		for job in json_data_copy['job_config']:
			# print(job)
			if(job['type'] == 'telosb'):
				job['binary_file'] = telosb_maintenance_binary_filename
			if(job['type'] == 'cc2650'):
				job['binary_file'] = cc2650_maintenance_binary_filename
		# burn_results = burn_motes(json_data_copy)

		burn_process = Process(target=burn_motes,args=([json_data_copy]))
		burn_process.start()
		#burn_process.join()
		sleep(0.1)
		# burn_results = burn_motes(json_data)
		# logger.info(result_id + " " +str(burn_results))
		# save_burn_log(json_data, burn_results)
		tmp_job_lock = fasteners.InterProcessLock('/tmp/tmp_job_lock_' + result_id)
		#while(1):
		#	x=
		tmp_job_lock.acquire(blocking=True)
		#	if(x): break
		#	print("waiting for job",result_id,"to be processed!")
		#	sleep(1)
		tmp_job_lock.release() # just make sure that the burning is done :)

		# mote_list_burnt = check_successful_burn(json_data_copy)

		logger.info("maintenance done: " + result_id)
		finish_job(json_data_copy, True)
	except:
		print(traceback.print_exc())

def process_job(json_data):

	global scheduler
	result_id = json_data['result_id']


	process_job_lock = FileLock("/tmp/" + result_id)
	with process_job_lock.acquire(timeout = PROCESS_JOB_LOCK_TIMEOUT, poll_intervall=PROCESS_JOB_LOCK_POLL_INTERVAL):
	# with FileLock("/tmp/" + result_id):

		# process_job_lock = fasteners.InterProcessLock('/tmp/process_job_lock_' + result_id)
		# process_job_lock.acquire(blocking=True)

		global running_jobs

		logger.info("processing job submitted by " + str(json_data['user']) + " result_id " + str(result_id))
		# sleep(GAP_BEFORE_STARTING_NEW_JOB)
		mote_list = []
		for i in range(len(json_data['job_config'])):
			 mote_list = mote_list + json_data['job_config'][i]['mote_list']
		deactive_motes(mote_list)

		burn_process = Process(target=burn_motes,args=([json_data]))
		burn_process.start()
		#burn_process.join()
		sleep(0.1)
		# burn_results = burn_motes(json_data)
		# logger.info(result_id + " " +str(burn_results))
		# save_burn_log(json_data, burn_results)
		tmp_job_lock = fasteners.InterProcessLock('/tmp/tmp_job_lock_' + result_id)
		#while(1):
		#	x=
		tmp_job_lock.acquire(blocking=True)
		#	if(x): break
		#	print("waiting for job",result_id,"to be processed!")
		#	sleep(1)
		tmp_job_lock.release() # just make sure that the burning is done :)


		##################################################################
		##################################################################
		######## CHECK ALSO IF JOB IS NOT CANCELLED BY NOW ###############
		##################################################################
		##################################################################
		mote_list_burnt = check_successful_burn(json_data)
		if(len(mote_list_burnt) > 0):# and job_is_not_cancelled_by_now):
			logger.warn(str(len(mote_list_burnt)) + '/' + str(len(mote_list)) + ' motes are successfully burn for job ' + result_id)
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

		# process_job_lock.release()

		# print('#############################################################################################')

def check_successful_burn(json_data):
	#global burn_results
	print("check success",json_data)
	motes_successfully_burnt = []
	burn_results =read_burn_log(json_data)
	print(str(burn_results))
	for key in burn_results["job_config"].keys():
		moteids = burn_results["job_config"][key].keys()
		for moteid in moteids:
			if(burn_results["job_config"][key][moteid].get('burn') == '1'):
				motes_successfully_burnt.append(moteid)
				print(moteid)
			else:
				logger.warn("check burn results " + json_data["result_id"]  + ": checking before burn results are available")
	burn_results.pop(json_data['result_id'], None)
	logger.warn("removing burn results for " + json_data['result_id'] + " from dict burn_results")
	return motes_successfully_burnt

def add_job_to_job_queue_and_scheduler(json_data):
	global first_run, jobs_queue, scheduler, hibernate
	result_id = json_data['result_id']
	if(hibernate):
		result = "0"
		logging.error("adding job during (from/to) hibernation process: " + resultid )
		return result

	if(first_run):
		# start_new_thread(check_scheduler,())
		first_run = 0
	try:
		job_queue_lock.acquire()

		# jobs_queue = pickle.load( open( "jobs_queue.p", "rb" ) )
		# scheduler = pickle.load( open( "scheduler.p", "rb" ) )

		jobs_queue[json_data['result_id']]={}
		jobs_queue[json_data['result_id']]['json_data']=json_data

		#########################################################################
		# events are distinguished based on time and not the event tuple ;)
		#########################################################################
		rnd = random.random()
		decimal_place = 1000000
		rnd_a_dp = (round(rnd * decimal_place))/decimal_place
		logger.info("rnd_a_dp: " + str(rnd_a_dp))
		# e_start = scheduler.enterabs(int(json_data['time']['from']) + GAP_BEFORE_STARTING_NEW_JOB + (round(random() * decimal_place))/decimal_place, 1, schedule_job, (json_data,))
		# e_finish = scheduler.enterabs(int(json_data['time']['to']) - GAP_BEFORE_STARTING_NEW_JOB + (round(random() * decimal_place))/decimal_place, 1, finish_job, (json_data,))
		logger.info("start time:" + str(int(json_data['time']['from']) + GAP_BEFORE_STARTING_NEW_JOB + rnd_a_dp))
		logger.info("end time:" + str(int(json_data['time']['from']) - GAP_BEFORE_STARTING_NEW_JOB + rnd_a_dp))
		e_start = scheduler.enterabs(int(json_data['time']['from']) + GAP_BEFORE_STARTING_NEW_JOB + rnd_a_dp, 1, schedule_job, (json_data,))
		e_finish = scheduler.enterabs(int(json_data['time']['to']) - GAP_BEFORE_STARTING_NEW_JOB + rnd_a_dp, 1, finish_job, (json_data,))

		# e_start = scheduler.enter(int(json_data['time']['from']), 1, schedule_job, (json_data,))
		# e_finish = scheduler.enter(int(json_data['time']['to']), 1, finish_job, (json_data,))
		
		jobs_queue[json_data['result_id']]['job_schedule_event'] = e_start
		jobs_queue[json_data['result_id']]['job_finish_event'] = e_finish
		logger.info("new job submitted by " + str(json_data['user']) + " added to job queue")

		# pickle.dump( jobs_queue, open( "jobs_queue.p", "wb" ) )
		# pickle.dump( scheduler, open( "scheduler.p", "wb" ) )

		job_queue_lock.release()
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "1"
	except:
		print(traceback.print_exc())
		print("SCHEDULER QUEUE:",scheduler.queue)
		return "0"


def cancel_job_from_queue(json_data):

	global scheduler, hibernate

	result_id = json_data['result_id']

	if(hibernate):
		result = "0"
		logging.error("cancelling job during (from/to) hibernation process: " + resultid )
		return result

	

	# process_job_lock = fasteners.InterProcessLock('/tmp/process_job_lock_' + result_id)
	# process_job_lock.acquire(blocking=True)

	process_job_lock = FileLock("/tmp/" + result_id) # make sure that job is not being processed at the same time... if already started
	with process_job_lock.acquire(timeout = PROCESS_JOB_LOCK_TIMEOUT, poll_intervall=PROCESS_JOB_LOCK_POLL_INTERVAL):

		global jobs_queue, running_jobs
		print("before cancel job with id", result_id ,scheduler.queue)
		logger.info("before cancel job with id " + result_id  + str(scheduler.queue))
		#lock
		
		result = "0"


		# tmp_job_lock = fasteners.InterProcessLock('/tmp/tmp_job_lock_' + result_id)
		# tmp_job_lock.acquire(blocking=True)
		# use blocking false with sleep!!!

		job_queue_lock.acquire()

		# jobs_queue = pickle.load( open( "jobs_queue.p", "rb" ) )
		# scheduler = pickle.load( open( "scheduler.p", "rb" ) )


		if(jobs_queue.get(result_id) != None):
			#job_queue_lock.release() # finish_job also needs that lock
			#now = time()
			job_time_from = int(jobs_queue[result_id]['json_data']['time']['from'])
			job_time_to = int(jobs_queue[result_id]['json_data']['time']['to'])
			json_data_full_tmp = dict(jobs_queue[result_id]['json_data'])

			# print("--------------------------------------------------------------------------------------")
			# print(jobs_queue[result_id]['json_data']['time']['from'], str(int(now)))
			# print("--------------------------------------------------------------------------------------")
			logger.warn("schedule event" + str(jobs_queue[result_id]['job_schedule_event']))
			logger.warn("finish event" + str(jobs_queue[result_id]['job_finish_event']))
			pop_job = True 
			if jobs_queue[result_id]['job_schedule_event'] not in scheduler.queue and jobs_queue[result_id]['job_finish_event'] in scheduler.queue:
				try:
					scheduler.cancel(jobs_queue[result_id]['job_finish_event'])
					# mote_list = []
					# for i in range(len(jobs_queue[result_id]['json_data']['job_config'])):
					# 	 mote_list = mote_list + jobs_queue[result_id]['json_data']['job_config'][i]['mote_list']
					# deactive_motes(mote_list)
					
					# if(result_id in running_jobs['active']):
					# 	running_jobs_lock.acquire()
					# 	running_jobs['active'].remove(result_id)
					# 	running_jobs_lock.release()

					scheduler.enterabs(int(time()) + GAP_TO_START_CLEANING_WHEN_CANCELLING_DURING_RUNNING, 2, finish_job, (json_data_full_tmp,))
					pop_job = False
					logger.info("job with result_id " +  result_id + ", to be cancelled, is in running state... trying to cancel...")

				except:
					logging.error("1. ---------------------------------")
					print(traceback.print_exc())
					# job finishing already...
					pass
					# scheduler.enterabs(int(time()) + 5, 1, finish_job, (json_data,))


			if jobs_queue[result_id]['job_schedule_event'] in scheduler.queue:
				try:
					scheduler.cancel(jobs_queue[result_id]['job_schedule_event'])
					logger.info("job schedule event, with result_id " +  result_id + ", was cancelled")
				# except ValueError:
				except:
					logging.error("2. ---------------------------------")
					print(traceback.print_exc())
					# job already started...
					pass
					# scheduler.enterabs(int(time()) + 5, 1, finish_job, (json_data,))
			
			if jobs_queue[result_id]['job_finish_event'] in scheduler.queue:
				try:
					scheduler.cancel(jobs_queue[result_id]['job_finish_event'])
					logger.info("job compiling/zipping event, with result_id " +  result_id + ", was cancelled")
					# scheduler.enterabs(int(time()), 1, finish_job, (json_data_full_tmp,))
				# except ValueError:
				except:
					logging.error("3. ---------------------------------")
					print(traceback.print_exc())
					pass # finishing job already...
					# job already started...
					# scheduler.enterabs(int(time()) + 5, 1, finish_job, (json_data,))

			if pop_job:
				jobs_queue.pop(result_id,None)

			# if(job_time_from + GAP_BEFORE_STARTING_NEW_JOB > int(time())):
			# 	scheduler.cancel(jobs_queue[result_id]['job_schedule_event'])
			# 	logger.info("job schedule event, with result_id " +  result_id + ", was cancelled")
			# if(job_time_to > int(time()) - GAP_BEFORE_STARTING_NEW_JOB):
			# 	scheduler.cancel(jobs_queue[result_id]['job_finish_event'])
			# 	logger.info("job compiling/zipping event, with result_id " +  result_id + ", was cancelled")
			# # print("after cancel job",scheduler.queue)

			# if(job_time_from + GAP_BEFORE_STARTING_NEW_JOB < int(time()) < job_time_to - GAP_BEFORE_STARTING_NEW_JOB):
			# 	logger.info("job with result_id " +  result_id + ", to be cancelled, is in running state")
			# 	finish_job(jobs_queue[result_id]['json_data']) #use job_queue_lock as well!!!!
			# 	#maintenance_after_finishing_job(jobs_queue[result_id]['json_data'])
			# 	#maintenance_after_finishing_job(json_data_tmp)			
			# 	'''
			# 	mote_list = []
			# 	for i in range(len(jobs_queue[result_id]['json_data']['job_config'])):
			# 		 mote_list = mote_list + jobs_queue[result_id]['json_data']['job_config'][i]['mote_list']
			# 	deactive_motes(mote_list)
				
			# 	if(result_id in running_jobs['active']):
			# 		running_jobs_lock.acquire()
			# 		running_jobs['active'].remove(result_id)
			# 		running_jobs_lock.release()

			# 	maintenance_after_finishing_job(jobs_queue[result_id]['json_data'])
			# 	'''

			logger.info("Job, with result_id " +  result_id + ", is being cancelled")
			#json_data_tmp = dict(jobs_queue[result_id]['json_data'])		
			#jobs_queue.pop(result_id,None)

			# pickle.dump( jobs_queue, open( "jobs_queue.p", "wb" ) )
			# pickle.dump( scheduler, open( "scheduler.p", "wb" ) )

			job_queue_lock.release()
			#maintenance_after_finishing_job(json_data_tmp)

			print("SCHEDULER QUEUE:",scheduler.queue)
			result = "1"
		else:
			logger.warn("trying to cancel job, with result_id " +  result_id + ", that does not exist")
			job_queue_lock.release()
			print("SCHEDULER QUEUE:",scheduler.queue)
			# result = "0"
		
		# process_job_lock.release()

		print("after cancel job with id", result_id ,scheduler.queue)
		logger.info("after cancel job with id" + result_id  + str(scheduler.queue))
		# job_queue_lock.release()
		# tmp_job_lock.release() 
	return result

@app.route("/hibernate", methods=['GET','POST'])
def hibernate():
	global hibernate
	hibernate = 1
	job_queue_lock.acquire()

	pickle.dump( jobs_queue, open( "jobs_queue.p", "wb" ) )
	pickle.dump( scheduler, open( "scheduler.p", "wb" ) )

	job_queue_lock.release()
	response={}
	response['hibernate']="SUCCESS"

	return str(response)


@app.route("/reload_jobs", methods=['GET','POST'])
def reload_jobs():
	global jobs_queue, scheduler, scheduler_down,hibernate
	response = {}
	response['message'] = "jobs reloaded!"	
	try:
		job_queue_lock.acquire()
		jobs_queue = pickle.load( open( "jobs_queue.p", "rb" ) )
		scheduler = pickle.load( open( "scheduler.p", "rb" ) )
		job_queue_lock.release()


		keys = list(jobs_queue.keys())
		logger.info(keys)
		for result_id in keys:
			print("#############################################################################")
			print(result_id, jobs_queue[result_id]['json_data']['time']['to'], str(time()))
			if(int(jobs_queue[result_id]['json_data']['time']['to']) < int(time()) + TIME_TO_EXECUTE_A_JOB*2): # start gap + run for at least gap + stop gap
				cancel_job_from_queue(jobs_queue[result_id]['json_data'])

		if scheduler_down:
			start_new_thread(check_scheduler,())
			scheduler_down = False
	except:
		response = {}
		response['message'] = "jobs NOT reloaded!"

	hibernate = 0
	return str(response)

@app.route("/show_jobs_queue", methods=['GET','POST'])
def show_jobs_queue():
	global jobs_queue
	return str(jobs_queue)

@app.route("/show_scheduler", methods=['GET','POST'])
def show_scheduler():
	global scheduler
	return str(scheduler.queue)

@app.route("/cancel_job", methods=['POST'])
def cancel_job():
	print("CANCEL JOB",colored(str(request.json),"red"))
	json_data = request.json
	logger.info("REQUEST: job with resultid " + json_data['result_id'] + " is called for cancelation")# + str(json_data['user']) + "@" + str(time()) + " to be running from " + json_data['time']['from'] + " to " + json_data['time']['to'])
	result = cancel_job_from_queue(json_data)
	response={}
	response['result_id']=json_data['result_id']
	response['action']='cancel_job'
	response['result']=result
	response['result']=1
	return str(response)

# @app.route("/cancel_job", methods=['POST'])
# def cancel_job():
# 	json_data = request.json
# 	response={}
# 	response['result_id']=json_data['result_id']
# 	response['action']='cancel_job'
# 	response['result']="1"
# 	return str(response)

@app.route("/active_users", methods=['GET','POST'])
def active_users():
	return str(active_users)

@app.route("/active_jobs", methods=['GET','POST'])
def active_jobs():
	return str(running_jobs)

@app.route("/get_burn_results", methods=['GET','POST'])
def get_burn_results():
	json_data = request.json
	print("/get_burn_results",json_data)
	data = read_burn_log(json_data)
	return str(data)

@app.route("/new_job", methods=['GET','POST'])
def new_job():
	global scheduler_down
	if scheduler_down:
		start_new_thread(check_scheduler,())
		scheduler_down = False

	print("NEW JOB",colored(str(request.json),"green"))
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

@app.route("/check_binary", methods=['POST'])
def check_binary():
	json_data = request.json #	{"binary_file":"beacon.sky", "type":"telosb"}
	binary_file = server_binaries_dir + json_data['binary_file']
	motetype = json_data['type']
	logger.info("checking binary file " + str(binary_file) + " for type " + str(motetype))
	if(run_jobs.check_binary_file(binary_file, motetype)):
		json_data['result'] = '1'
	else:
		json_data['result'] = '0'
	return str(json_data)



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
	# start_new_thread(check_scheduler,())
	scheduler_down = True
	
	###############################################################################################################
	#### get_data_from_nodes
	###############################################################################################################
	with Manager() as manager:


		manager_proxy_nodes_status = manager.dict()
		active_users = manager.dict()
		active_motes = manager.dict()
		# scheduler_dict = manager.dict()
		# scheduler_dict['scheduler'] = scheduler

		aggregator_server = Process(target=listen,args=([active_users,active_motes]))
		aggregator_server.start()
		sleep(2)

		get_data_from_nodes_server = Process(target=check_nodes_status_from_db,args=([manager_proxy_nodes_status,active_users,active_motes]))
		get_data_from_nodes_server.start()

		sub_nodeid_rt_input_server = Process(target=accept_rt_input,args=([active_users,active_motes]))
		sub_nodeid_rt_input_server.start()

		app_server = Process(target=app.run,args=())
		app_server.start()

		# scheduler_server = Process(target=run_scheduler,args=([scheduler_dict]))
		# scheduler_server.start()

		get_data_from_nodes_server.join()

		# scheduler.run(blocking=True)

