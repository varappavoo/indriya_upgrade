#!/usr/bin/python3
import os
from config import *

job_id = "1"
time_from = 1503460470000000000
time_to = 1503461290502605824
nodes_set = ['111','222']

for nodeid in nodes_set:
	command_get_data_for_job = "influx -database " + dbname + " -format csv -execute \"select * from " + table + " where time > " + str(time_from) + " and time < " + str(time_to) + " and nodeid='" + nodeid + "'\" -username '" + dbuser 
	+ "' -password '" + dbuser_password + "' > data_jobid_" + job_id + "_" + nodeid + ".csv"
	print(os.system(command_get_data_for_job))

command_zip_data_for_job = "zip data_jobid_1.zip data_jobid_*.csv"
print(os.system(command_zip_data_for_job))