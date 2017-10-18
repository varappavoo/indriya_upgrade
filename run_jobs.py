#!/usr/bin/python3

import json
from run_config import *
import subprocess
import _thread, threading
from time import sleep

import logging
import logging.config


logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('run_jobs')

burn_results = {}
with open('db_nodes_telosb.json') as json_data:
	json_db_nodes_telosb = json.load(json_data)

class ThreadBurnMote (threading.Thread):
	def __init__(self, motetype, moteref, scp_command, ssh_burn_command):
		threading.Thread.__init__(self)
		self.motetype = motetype
		self.moteref = moteref
		self.scp_command = scp_command
		self.ssh_burn_command = ssh_burn_command
	def run(self):
		print ("Starting " + self.moteref)
		execute_job(self.motetype, self.moteref, self.scp_command, self.ssh_burn_command)
		print ("Exiting " + self.moteref)

def run_cmd(command, success_identifier):
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE ) # stdout=subprocess.PIPE, shell=True)
	(output, err) = p.communicate()
	output = output.decode("utf-8")
	err = err.decode("utf-8")
	if(output.find(success_identifier) > -1 or err.find(success_identifier) > -1):
		print("SUCCESS!!")
		logger.info("SUCCESS:" + command)
		return True
	else:
		print("FAILURE!!")
		logger.warning("FAILURE:" + command)
		return False

def execute_job(motetype, moteref,scp_command,ssh_burn_command):# scp and burn
	global burn_results
	if burn_results['job_config'].get(motetype) == None:
		burn_results['job_config'][motetype] = {}
	burn_results['job_config'][motetype][moteref]={}
	print(burn_results)
	burn_results['job_config'][motetype][moteref]['scp'] = "1" if(run_cmd(scp_command, "Exit status 0")) else "0"
	if burn_results['job_config'][motetype][moteref]['scp'] == "1":
		burn_results['job_config'][motetype][moteref]['burn'] = "1" if(run_cmd(ssh_burn_command, "Programming: OK")) else "0"
	else:
		burn_results['job_config'][motetype][moteref]['burn'] = "0"
		logger.warning("Not attempting to burn as SCP was unsuccessful: \n" + scp_command)
	print(burn_results)



def schedule_job(json_jobs_waiting):
		# with open('jobs_waiting.json') as json_data:
		global burn_results
		# json_jobs_waiting = json.load(json_data)
		# json_jobs_waiting = json.load(json_data)
		# print()
		print(json_jobs_waiting)
		burn_results['job_config']={}
		for job in json_jobs_waiting['job_config']:
			print(job)
			burn_results['result_id']=json_jobs_waiting['result_id']

			if(job['type'] == 'telosb'):
				for mote in job['mote_list']:
					
					print(mote, json_db_nodes_telosb[mote])
					scp_command = "scp -v " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_db_nodes_telosb[mote]['gateway'] \
										+ ":" + gateway_binaries_dir
					ssh_burn_command = "ssh " + gateway_user + "@" +json_db_nodes_telosb[mote]['gateway'] + " '" + gateway_source_dir + "burn_telosb_test.py " \
										+  "telosb " + json_db_nodes_telosb[mote]['serial_id'] + " " + gateway_binaries_dir + job['binary_file']  + "'"
					print(scp_command)
					print(ssh_burn_command)
					ThreadBurnMote(job['type'],mote,scp_command,ssh_burn_command).start()


		while(threading.activeCount() > 1): # main thread also counts
			print(threading.enumerate())
			sleep(1)

		print(burn_results)
		return burn_results

