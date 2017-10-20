#!/usr/bin/python3
import random
import fasteners
import subprocess

def run_cmd(command, success_identifier=""):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE ) # stdout=subproc$
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

def generate_password():
	characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
	password = ''
	for i in range(16):
		password += random.choice(characters)
	return password


def add_new_mqtt_user(user):
	password = generate_password()
	success = 0
	mosquitto_lock = fasteners.InterProcessLock('/tmp/tmp_mosquitto_lock_file')
	while 1:
			mosquitto_lock_acquired = mosquitto_lock.acquire(blocking=False)
			#try:
			if(mosquitto_lock_acquired):
				# update mosquitto_passwd, mosquitto_acl
				mosquitto_passwd_file = "/home/cirlab/indriya_upgrade/mosquitto_passwd"
				mosquitto_acl_file = "/home/cirlab/indriya_upgrade/mosquitto_acl"
				with open(mosquitto_acl_file, 'a') as f:
					f.write('\n')
					f.write('user ' + user + '\n')
					f.write('topic readwrite ' + user + '/#\n')
					f.close()
				mos_pass_cmd = "mosquitto_passwd -b " + mosquitto_passwd_file + " " + user + " " + password
				run_cmd(mos_pass_cmd)
				success = 1
				#print("releasing")
				mosquitto_lock.release()
				#print("released")
				break
			else:
				sleep(1)
			#finally:
			#mosquitto_lock.release()
	if(success):
		return password
	else:
		return None
	#pass

