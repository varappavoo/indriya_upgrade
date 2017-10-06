#!/usr/bin/python3

import subprocess

########################
####### DEACTIVATE NODE BEFORE BURNING, SET GET DATA TO 0 IN DBNODES.CSV
######################
def run_cmd(command):
	p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	(output, err) = p.communicate()
	output = str.split(str(output), ' ')
	print(output)

def get_serial_address(nodeid_lookup):
	found=False
	nodes_status_file = open("influxdb/db_nodes.csv",'r')
	line = nodes_status_file.readline() # header
	line = nodes_status_file.readline()
	while(line!="" and not found):
		line_split = line.split(",")
		print(line_split)
		nodeid = line_split[0]
		if(nodeid_lookup == nodeid):
			found = True
			mote_serial_address = (line_split[4]).strip()
			break
		line = nodes_status_file.readline()

	if(found):
		return mote_serial_address
	else:
		return 0



def burn_binary(mote_type, nodeid, binary_file):
	if(mote_type == 'telosb'):
		#msp430-bsl-telosb -p + /dev/serial/by-id/usb-XBOW_Crossbow_Telos_Rev.B_XBSF8O49-if00-port0 -er dyn_sample.sky
		mote_serial_address = get_serial_address(nodeid)
		print(nodeid, mote_serial_address)
		if(mote_serial_address == 0):
			print("NO mote_serial_address FOUND FOR",nodeid)
		else:
			command = "msp430-bsl-telosb -p " + mote_serial_address + " -er " + binary_file
			run_cmd(command)

burn_binary("telosb", "205", "telosb_bin/beacon.sky")
# burn_binary("telosb", "205", "telosb_bin/dyn_sample.sky")
