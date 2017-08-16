#!/usr/bin/python3
from influxdb import InfluxDBClient
from random import randint
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
print("Create a retention policy")
client.create_retention_policy('one_day_retention_policy', '1d', 3, default=True)

print(time())
for i in range(1000):
	
	value = randint(1,1000)

	# print("Create database: " + dbname)
	# client.create_database(dbname)
	json_body = [
	    {
	    	"measurement": table,
	        "tags": {"nodeid": str(nodeid)},
	        "fields": {"value": 'some random data_' + str(value)}
	    }
	]

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

	# result = client.write(insert_statement,protocol = 'line')
	result =  client.write_points(json_body)


# result =  client.write_points(data)
print(result)


# result = client.query('select nodeid,value from test;')
# print(result)
print(time())