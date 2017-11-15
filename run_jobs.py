#!/usr/bin/python3

import json
from run_config import *
import subprocess
import _thread, threading
from time import sleep

import logging
import logging.config
import fasteners

from zip_job_data import *

MAX_RETRIES_BURN = 3
WAIT_BEFORE_RETRY = 5
MAX_TIME_TO_WAIT_FOR_LOCK_ON_MOTE = 30

logging.config.fileConfig('logging.conf')

# create logger
logger = logging.getLogger('run_jobs')

burn_results = {}
with open('nodes_virt_id_phy_id.json') as json_data:
	json_nodes_virt_id_phy_id = json.load(json_data)

class ThreadBurnMote (threading.Thread):
	def __init__(self, result_id, motetype, moteref, scp_command, ssh_burn_command, elf_file):
		threading.Thread.__init__(self)
		self.result_id = result_id
		self.motetype = motetype
		self.moteref = moteref
		self.scp_command = scp_command
		self.ssh_burn_command = ssh_burn_command
		self.elf_file = elf_file
		self.count = 0
	def run(self):
		print ("Starting " + self.moteref)
		logger.warn("locking " + self.moteref)
		tmp_mote_lock = fasteners.InterProcessLock('/tmp/tmp_mote_lock_' + self.moteref)

		while(True):
			x = tmp_mote_lock.acquire(blocking=False)
			try:
				if x:
					logger.warn('got lock on mote ' + self.moteref)
					# x = tmp_mote_lock.acquire(blocking=True)
					execute_job(self.result_id, self.motetype, self.moteref, self.scp_command, self.ssh_burn_command, self.elf_file)
					tmp_mote_lock.release()
					logger.warn("unlocking " + self.moteref)
					print ("Exiting " + self.moteref)
					break
				else:
					self.count += 1 
					logger.warn('not getting lock on mote ' + self.moteref + ', try ' + str(self.count))
					if self.count < MAX_TIME_TO_WAIT_FOR_LOCK_ON_MOTE:
						sleep(1)
					else:
						global burn_results
						result_id = self.result_id
						motetype = self.motetype
						moteref = self.moteref
						if burn_results[result_id]['job_config'].get(motetype) == None:
							burn_results[result_id]['job_config'][motetype] = {}
						burn_results[result_id]['job_config'][motetype][moteref]={}
						burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] = "0"
						burn_results[result_id]['job_config'][motetype][moteref]['burn'] = "0"
						burn_results[result_id]['job_config'][motetype][moteref]['error'] = "could not lock mote"
						break
			except:
				traceback.print_stack()
				global burn_results
				if burn_results[result_id]['job_config'].get(motetype) == None:
					burn_results[result_id]['job_config'][motetype] = {}
				burn_results[result_id]['job_config'][motetype][moteref]={}
				burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] = "0"
				burn_results[result_id]['job_config'][motetype][moteref]['burn'] = "0"
				burn_results[result_id]['job_config'][motetype][moteref]['error'] = "could not lock mote"




def run_cmd(command, success_identifier, success=True):
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE ) # stdout=subprocess.PIPE, shell=True)
	(output, err) = p.communicate()
	output = output.decode("utf-8")
	err = err.decode("utf-8")
	if(success and (output.find(success_identifier) > -1 or err.find(success_identifier) > -1)):
		print("SUCCESS!!")
		logger.info("SUCCESS:" + command)
		return True
	elif(not success and (not(output.find(success_identifier) > -1) or not(err.find(success_identifier) > -1))): # here we have an identifier for failure...
		print("SUCCESS!!")
		logger.info("SUCCESS:" + command)
		return True
	else:
		print("FAILURE!!")
		logger.warning("FAILURE:" + command + "\n\n" + output + "\n" + err)
		return False

def check_binary_file(elf_file, motetype):
	if motetype == 'telosb':
		file_type = 'ELF 32-bit LSB executable, TI msp430, version 1, statically linked, not stripped'
	elif motetype == 'cc2650':
		file_type = 'ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), statically linked, not stripped'
	else:
		logger.warn("system does not support for binary file of type " + motetype)
		return False
	return run_cmd('file ' + elf_file, file_type)

def execute_job(result_id, motetype, moteref,scp_command,ssh_burn_command, elf_file):# scp and burn
	global burn_results
	if burn_results[result_id]['job_config'].get(motetype) == None:
		burn_results[result_id]['job_config'][motetype] = {}
	burn_results[result_id]['job_config'][motetype][moteref]={}
	print(burn_results[result_id])

	count_burn_tries = 1

	try:
		# burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] = "1" if(run_cmd(scp_command, "Exit status 0")) else "0"
		if(check_binary_file(elf_file, motetype)):
			logger.info("file check passed: " + elf_file + " " + motetype)
			burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] = "1" if(run_cmd(scp_command, "rsync error", False)) else "0"
			if burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] == "1":
				burn_done = "0"
				while(count_burn_tries <= MAX_RETRIES_BURN and burn_done == "0"):
					logger.warning(moteref + " - BURNING TRY:" + str(count_burn_tries))
					if motetype == 'telosb':
						burn_done = "1" if(run_cmd(ssh_burn_command, "Programming: OK")) else "0"
					elif motetype == 'cc2650':
						burn_done = "1" if(run_cmd(ssh_burn_command, "Failed:", False)) else "0"
					count_burn_tries = count_burn_tries + 1
					if count_burn_tries > 1:
						sleep(WAIT_BEFORE_RETRY)
				burn_results[result_id]['job_config'][motetype][moteref]['burn'] = burn_done
			else:
				burn_results[result_id]['job_config'][motetype][moteref]['burn'] = "0"
				logger.warning("Not attempting to burn as SCP was unsuccessful: \n" + scp_command)
			print(burn_results[result_id])
		else:
			logger.info("file check FAILED: " + elf_file + " " + motetype)
			burn_results[result_id]['job_config'][motetype][moteref]['cluster_rsync'] = "0"
			burn_results[result_id]['job_config'][motetype][moteref]['burn'] = "0"
			burn_results[result_id]['job_config'][motetype][moteref]['error'] = "file format not supported for this mote"
	except:
		burn_results[result_id]['job_config'][motetype][moteref]['error'] = "job execution exception"
		traceback.print_stack()

def schedule_job(json_jobs_waiting):
		global burn_results
		result_id = json_jobs_waiting['result_id']

		tmp_job_lock = fasteners.InterProcessLock('/tmp/tmp_job_lock_' + result_id)
		logger.info("trying to lock job for " + result_id)
		tmp_job_lock.acquire(blocking=True)
		logger.info("obtained to lock job for " + result_id)

		burn_results[result_id] = {}
		# with open('jobs_waiting.json') as json_data:
		# json_jobs_waiting = json.load(json_data)
		# json_jobs_waiting = json.load(json_data)
		# print()

		num_threads = threading.activeCount()
		# num_threads_new = 0
		print(json_jobs_waiting)
		burn_results[result_id]['job_config']={}
		all_threads = []
		for job in json_jobs_waiting['job_config']:
			print(job)
			burn_results[result_id]['result_id']=json_jobs_waiting['result_id']

			if(job['type'] == 'telosb'):
				for mote in job['mote_list']:
					
					print(mote, json_nodes_virt_id_phy_id[mote])
					# scp_command = "scp -v " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_nodes_virt_id_phy_id[mote]['gateway'] \
										# + ":" + gateway_binaries_dir

					scp_command = "rsync -av --ignore-existing " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_nodes_virt_id_phy_id[mote]['gateway'] \
										+ ":" + gateway_binaries_dir
					ssh_burn_command = "ssh " + gateway_user + "@" +json_nodes_virt_id_phy_id[mote]['gateway'] + " '" + gateway_source_dir + "burn_telosb_test.py " \
										+  "telosb " + json_nodes_virt_id_phy_id[mote]['serial_id'] + " " + gateway_binaries_dir + job['binary_file']  + "'"
					print(scp_command)
					logger.warn(scp_command)
					print(ssh_burn_command)
					logger.warn(ssh_burn_command)
					elf_file = server_binaries_dir + job['binary_file']
					t = ThreadBurnMote(result_id,job['type'],mote,scp_command,ssh_burn_command, elf_file)
					# t.start()
					# t.join()
					# num_threads_new = num_threads_new + 1
					all_threads.append(t)


			if(job['type'] == 'cc2650'):
				for mote in job['mote_list']:
					
					print(mote, json_nodes_virt_id_phy_id[mote])
					# scp_command = "scp -v " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_nodes_virt_id_phy_id[mote]['gateway'] \
										# + ":" + gateway_binaries_dir
					scp_command = "rsync -av --ignore-existing " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_nodes_virt_id_phy_id[mote]['gateway'] \
										+ ":" + gateway_binaries_dir
					ssh_burn_command = "ssh " + gateway_user + "@" +json_nodes_virt_id_phy_id[mote]['gateway'] + \
										" '/home/cirlab/flash_sensortag_linux_64/dslite.sh -v -c "\
										 + json_nodes_virt_id_phy_id[mote]['flash_file'] + " -f " + gateway_binaries_dir + job['binary_file']  + "'"
					print(scp_command)
					print(ssh_burn_command)
					
					elf_file = server_binaries_dir + job['binary_file']
					t = ThreadBurnMote(result_id,job['type'],mote,scp_command,ssh_burn_command, elf_file)
					# t.start()
					# t.join()
					# num_threads_new = num_threads_new + 1
					all_threads.append(t)

		print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
		#while threading.activeCount() > num_threads:
		#	sleep(1)

		for t in all_threads:
			t.start()

		for t in all_threads:
			t.join()
		# while(threading.activeCount() > 1): # main thread also counts
		# 	# print(threading.enumerate())
		# 	print("run_jobs:schedule_job:threading.activeCount",threading.activeCount())
		# 	sleep(1)

		print(burn_results[result_id])
		logger.info(json_jobs_waiting['result_id'] + str(burn_results[result_id]))
		logger.warn(burn_results)
		results = burn_results[result_id]
		#burn_results.pop(result_id, None)

		save_burn_log(json_jobs_waiting, burn_results)
		logger.info("save burn results_1:" + str(json_jobs_waiting))
		logger.info("save burn results_2:" + str(burn_results))
		tmp_job_lock.release()

		return results

