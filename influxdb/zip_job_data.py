#!/usr/bin/python3
import os

time_from = 0
time_to = 0
nodes_set = ['111','222']


command_get_data_for_job = "influx -database experiment -format csv -execute 'select * from test where time > 1503460470000000000 and time < 1503461290502605824 and nodeid='111'' -username indriya_admin -password 'in@fluxis!50Xfaster' > data_jobid_1.csv"
command_zip_data_for_job = "zip data_jobid_1.zip data_jobid_1.csv"
print(os.system(command_get_data_for_job))
print(os.system(command_zip_data_for_job))