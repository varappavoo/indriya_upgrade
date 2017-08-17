#!/usr/bin/python3
from influxdb import InfluxDBClient
from random import randint
import sys
user = 'root'
password = 'root'
dbname = 'example'
dbuser = 'lenovo'
dbuser_password = 'enelongpasswordsa'
table = 'test'
host='localhost'
port=8086
nodeid = 333


from time import time,sleep
from datetime import datetime


client = InfluxDBClient(host, port, dbuser, dbuser_password, dbname)
# print("Create a retention policy")
# client.create_retention_policy('one_day_retention_policy', '1d', 3, default=True)

nodeid=sys.argv[1]
value=sys.argv[2]

start = time()
tmp_time = start

json_body = []
for i in range(1001):
	
	# value = randint(1,10)
	# print("Create database: " + dbname)
	# client.create_database(dbname)

	current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

	sleep(0.00001)
	json_body.append({
	    	"measurement": table,
	    	"time": current_time,
	        # "tags": {"nodeid": str(nodeid)},
	        # "fields": {"data": '1234567890123456789012345678901234567890_' + str(value)}
	        # "fields": {"ts": time(),"data": '123456789012345678901234567890_' + str(value)}
	        "fields": {"nodeid": str(nodeid),"data": '1234567890123456789012345678901234567890_' + str(value)}
	    })

	# if(i%100==0):
	now = time()
	if(now - tmp_time >= 1 or i%250==0):
		print(i)
		result =  client.write_points(json_body,time_precision='u')	
		print(result)
		# result =  client.write_points(json_body)	
		json_body = []
		tmp_time = now
	# measurement = {}
	# measurement['measurement'] = 'test'
	# measurement['tags'] = {}
	# measurement['fields'] = {}
	# measurement['tags']['nodeid'] = str(nodeid)
	# measurement['fields']['value'] = str(value)

	# data = [
	#   {"points":[[nodeid,value],[nodeid,value+10]],
	#    "name":table,
	#    "fields":["nodeid", "value"]
	#   }
	# ]
	# db.write_points(data)

	# print("inserting",value)

	# insert_statement = 'insert ' + table +',nodeid=' + str(nodeid) + ' value="some random data_' + str(value) + '";'
	# insert_statement = table +',nodeid=' + str(nodeid) + ' value="some random data_' + str(value) + '";'
	# print(insert_statement)

	# result = client.write(measurement)
	#,protocol = 'line')
	
	# result =  client.write(json_body, protocol='line')

# result =  client.write_points(data)
# print(result)


# result = client.query('select nodeid,value from test;')
# print(result)
print("time taken", time()-start)