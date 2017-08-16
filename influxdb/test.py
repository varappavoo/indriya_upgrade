#!/usr/bin/python3
from influxdb import InfluxDBClient
from random import randint
import sys
user = 'root'
password = 'root'
dbname = 'example'
dbuser = ''
dbuser_password = ''
table = 'test'
host='localhost'
port=8086
nodeid = 333


from time import time



client = InfluxDBClient(host, port, dbuser, dbuser_password, dbname)
# print("Create a retention policy")
# client.create_retention_policy('one_day_retention_policy', '1d', 3, default=True)

value=sys.argv[1]

start = time()

for i in range(10):
	
	# value = randint(1,10)
	

	# print("Create database: " + dbname)
	# client.create_database(dbname)


	json_body = [
	    {
	    	"measurement": table,
	    	# "time": time()*10000000,
	        "tags": {"nodeid": str(i%10)},
	        "fields": {"value": 'some random data_' + str(value)}
	    }
	]

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
	result =  client.write_points(json_body,time_precision='u')
	# result =  client.write(json_body, protocol='line')


# result =  client.write_points(data)
print(result)


# result = client.query('select nodeid,value from test;')
# print(result)
print("time taken", time()-start)