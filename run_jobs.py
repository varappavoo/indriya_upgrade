#!/usr/bin/python3

import json
from run_config import *
import subprocess
import _thread, threading
from time import sleep

burn_results = {}

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
	# print("voila",output)
	# print("voila",err)
	output = output.decode("utf-8")
	err = err.decode("utf-8")
	if(output.find(success_identifier) > -1 or err.find(success_identifier) > -1):
		print("SUCCESS!!")
		return True
	else:
		print("FAILURE!!")
		return False

def execute_job(motetype, moteref,scp_command,ssh_burn_command):# scp and burn
	global burn_results
	if burn_results['job_config'].get(motetype) == None:
		burn_results['job_config'][motetype] = {}
	burn_results['job_config'][motetype][moteref]={}
	print(burn_results)
	burn_results['job_config'][motetype][moteref]['scp'] = "1" if(run_cmd(scp_command, "Exit status 0")) else "0"
	burn_results['job_config'][motetype][moteref]['burn'] = "1" if(run_cmd(ssh_burn_command, "Programming: OK")) else "0"
	print(burn_results)

with open('db_nodes_telosb.json') as json_data:
	json_db_nodes_telosb = json.load(json_data)
	# print(json_db_nodes_telosb.keys())
	# print(json_db_nodes_telosb)

	# with open('db_nodes_sensortag.json') as json_data:
	# 	json_db_nodes_sensortag = json.load(json_data)
	# 	print(json_db_nodes_sensortag.keys())
	# 	print(json_db_nodes_sensortag)


	

	with open('jobs_waiting.json') as json_data:
		global burn_results
		json_jobs_waiting = json.load(json_data)
		# print()
		print(json_jobs_waiting)
		burn_results['job_config']={}
		for job in json_jobs_waiting['job_config']:
			print(job)
			burn_results['result_id']=json_jobs_waiting['result_id']

			# burn_results['job_config']={}
			if(job['type'] == 'telosb'):

				# if burn_results['job_config'].get('telosb') == None:
				# 	burn_results['job_config']['telosb'] = {}
				for mote in job['mote_list']:
					
					print(mote, json_db_nodes_telosb[mote])
					scp_command = "scp -v " + server_binaries_dir + job['binary_file'] + " "  + gateway_user + "@" + json_db_nodes_telosb[mote]['gateway'] \
										+ ":" + gateway_binaries_dir
					ssh_burn_command = "ssh " + gateway_user + "@" +json_db_nodes_telosb[mote]['gateway'] + " '" + gateway_source_dir + "burn_telosb_test.py " \
										+  "telosb " + json_db_nodes_telosb[mote]['serial_id'] + " " + gateway_binaries_dir + job['binary_file']  + "'"
					print(scp_command)
					# burn_results['job_config']['telosb'][mote]['scp'] = "1" if(run_cmd(scp_command, "Exit status 0")) else "0"
					print(ssh_burn_command)
					# burn_results['job_config']['telosb'][mote]['burn'] = "1" if(run_cmd(ssh_burn_command, "Programming: OK")) else "0"
					# run_cmd(ssh_burn_command, "Programming: OK")
					# _thread.start_new_thread( execute_job, (scp_command, ssh_burn_command, ) )
					ThreadBurnMote(job['type'],mote,scp_command,ssh_burn_command).start()


	while(threading.activeCount() > 1): # main thread also counts
		print(threading.enumerate())
		sleep(1)

	print(burn_results)

# ssh gateway1 '/home/cirlab/indriya_upgrade/burn_telosb_test.py telosb /dev/serial/by-id/usb-XBOW_Crossbow_Telos_Rev.B_XBSF8O49-if00-port0 /home/cirlab/indriya_upgrade/telosb_bin/dyn_sample.sky'
# "binary_file":"beacon.sky", "type":"telosb", "mote_list":["211","235"]