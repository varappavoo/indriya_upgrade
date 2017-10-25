#!/usr/bin/python3

import json
from run_config import *
import subprocess
import _thread, threading
from time import sleep

import logging
import logging.config
import fasteners

MAX_RETRIES_BURN = 3
WAIT_BEFORE_RETRY = 5

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('run_jobs')

burn_results = {}
with open('nodes_virt_id_phy_id.json') as json_data:
	json_nodes_virt_id_phy_id = json.load(json_data)

class ThreadBurnMote (threading.Thread):
	def __init__(self, motetype, moteref, scp_command, ssh_burn_command):
		threading.Thread.__init__(self)
		self.motetype = motetype
		self.moteref = moteref
		self.scp_command = scp_command
		self.ssh_burn_command = ssh_burn_command
	def run(self):
		print ("Starting " + self.moteref)
		logger.warn("locking " + self.moteref)
		tmp_mote_lock = fasteners.InterProcessLock('/tmp/tmp_mote_lock_' + self.moteref)
		x = tmp_mote_lock.acquire(blocking=True)
		execute_job(self.motetype, self.moteref, self.scp_command, self.ssh_burn_command)
		tmp_mote_lock.release()
		logger.warn("unlocking " + self.moteref)
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
	# global burn_results
	if burn_results['job_config'].get(motetype) == None:
		burn_results['job_config'][motetype] = {}
	burn_results['job_config'][motetype][moteref]={}
	print(burn_results)

	count_burn_tries = 1

	burn_results['job_config'][motetype][moteref]['scp'] = "1" if(run_cmd(scp_command, "Exit status 0")) else "0"
	if burn_results['job_config'][motetype][moteref]['scp'] == "1":
		burn_done = "0"
		while(count_burn_tries <= MAX_RETRIES_BURN and burn_done == "0"):
			logger.warning(moteref + " - BURNING TRY:" + str(count_burn_tries))
			burn_done = "1" if(run_cmd(ssh_burn_command, "Programming: OK")) else "0"
			count_burn_tries = count_burn_tries + 1
			if count_burn_tries > 1:
				sleep(WAIT_BEFORE_RETRY)
		burn_results['job_config'][motetype][moteref]['burn'] = burn_done
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
		num_threads = threading.activeCount()
		# num_threads_new = 0
		print(json_jobs_waiting)
		burn_results['job_config']={}
		all_threads = []
		for job in json_jobs_waiting['job_config']:
			print(job)
			burn_results['result_id']=json_jobs_waiting['result_id']

			if(job['type'] == 'telosb'):
				for mote in job['mote_list']:
					
					print(mote, json_nodes_virt_id_phy_id[mote])
					scp_command = "scp -v " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_nodes_virt_id_phy_id[mote]['gateway'] \
										+ ":" + gateway_binaries_dir
					ssh_burn_command = "ssh " + gateway_user + "@" +json_nodes_virt_id_phy_id[mote]['gateway'] + " '" + gateway_source_dir + "burn_telosb_test.py " \
										+  "telosb " + json_nodes_virt_id_phy_id[mote]['serial_id'] + " " + gateway_binaries_dir + job['binary_file']  + "'"
					print(scp_command)
					print(ssh_burn_command)
					ThreadBurnMote(job['type'],mote,scp_command,ssh_burn_command).start()
					# num_threads_new = num_threads_new + 1
					# all_threads.append(t)

		print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
		while threading.activeCount() > num_threads:
			sleep(1)
		# for t in all_threads:
		# 	t.join()


		# while(threading.activeCount() > 1): # main thread also counts
		# 	# print(threading.enumerate())
		# 	print("run_jobs:schedule_job:threading.activeCount",threading.activeCount())
		# 	sleep(1)

		print(burn_results)
		return burn_results

