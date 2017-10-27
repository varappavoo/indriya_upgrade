#!/usr/bin/python3
import os
from config import *
from run_config import *

import subprocess
import json
# job_id = "1"
# time_from = 1503460470000000000
# time_to = 1503461290502605824
# nodes_set = ['111','222']
# directory = 'packed_data/'
import logging
import traceback

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('zip_result_data')


TIME_GAP_BETWEEN_JOBS_FOR_ZIPPING_SECS = 5

def run_cmd(command, success_identifier=""):
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE ) # stdout=subprocess.PIPE, shell=True)
	(output, err) = p.communicate()
	output = output.decode("utf-8")
	err = err.decode("utf-8")
	print(output,err)
	if(output.find(success_identifier) > -1 or err.find(success_identifier) > -1):
		print("SUCCESS!!")
		#logger.info("SUCCESS:" + command)
		return True
	else:
		print("FAILURE!!")
		#logger.warning("FAILURE:" + command)
		return False

def zip_data_for_result(json_data):
	result_id = json_data['result_id']
	mote_list = []
	for i in range(len(json_data['job_config'])):
		mote_list = mote_list + json_data['job_config'][i]['mote_list']
	
	working_dir = RESULT_DIRECTORY + result_id + "/"
	run_cmd("mkdir -p " + working_dir)
	
	time_from = (int(json_data['time']['from']) + TIME_GAP_BETWEEN_JOBS_FOR_ZIPPING_SECS) * pow(10,9)
	time_to = (int(json_data['time']['to']) - TIME_GAP_BETWEEN_JOBS_FOR_ZIPPING_SECS) * pow(10,9)
	
	for nodeid in mote_list:
		command_get_data_for_job = "influx -database " + dbname + " -format csv -execute \"select * from " + table + \
		" where time > " + str(time_from) + " and time < " + str(time_to) + " and nodeid='" + nodeid + "'\" -username '" + dbuser + \
		"' -password '" + dbuser_password + "' > " + working_dir + nodeid + ".csv"
		print(command_get_data_for_job)
		print(os.system(command_get_data_for_job))

	command_zip_data_for_job = "zip -j " + working_dir + result_id + ".zip " + working_dir + "*"
	logger.info("zipping file for " + result_id + " :" + command_zip_data_for_job)
	print(os.system(command_zip_data_for_job))
	
	command_cp_to_www = "cp " + working_dir + result_id + ".zip " + RESULT_DIRECTORY_WWW
	logger.info("copying result of " + result_id + " to www folder : " + command_cp_to_www)
	run_cmd(command_cp_to_www)
	
	

	print(command_zip_data_for_job)

def save_burn_log(json_data, burn_results):

	result_id = json_data['result_id']
	working_dir = RESULT_DIRECTORY + result_id + "/"
	run_cmd("mkdir -p " + working_dir)
	filename =  working_dir + result_id +".log.json"
	# logger.info("TODO: save burn log file: " + filename)
	with open(filename,"w") as file_output:
		 json.dump(burn_results, file_output)
		 logger.info("burn log file saved: " + filename)
	return 1	

def read_burn_log(json_data):

	result_id = json_data['result_id']
	working_dir = RESULT_DIRECTORY + result_id + "/"
	run_cmd("mkdir -p " + working_dir)
	filename =  working_dir + result_id +".log.json"
	# logger.info("TODO: save burn log file: " + filename)
	burn_results = "{}"
	try:

		with open(filename,"r") as file_input:
			burn_results = json.load(file_input)
			burn_results = burn_results[list(burn_results.keys())[0]]
			# logger.info("burn log file saved: " + filename)
			# burn_results = json.loads(file_input.readlines()[0])
			# burn_results = burn_results[burn_results.key()]
			# burn_results = file_input.readlines()[0]

	except:
		burn_results = "{}"
		traceback.print_stack()
	return burn_results

#with open('alice_jobs.json') as data_file:    
#	json_data = json.load(data_file)
#zip_data_for_result(json_data)
