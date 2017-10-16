#!/bin/bash 
COUNTER=0
while [  $COUNTER -lt 10 ]; do
	# echo The counter is $COUNTER
	# influx -execute 'insert test,nodeid="111" value="not so random!10";' -database example
	curl -i -XPOST 'http://localhost:8086/write?db=example' --data-binary 'test,type="stag",nodeid="222" value="this is from curl 1000"'
	let COUNTER=COUNTER+1 
done