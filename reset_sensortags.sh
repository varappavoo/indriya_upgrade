#!/bin/bash
cmd = "sudo ./xdsdfu -e"
$cmd
for (( counter = 0; counter <= 20; counter++ ))
do
	echo "sudo ./xdsdfu  -m -i $counter"
	cmd="sudo ./xdsdfu  -m -i $counter"
	eval $cmd
done
sleep 5
for (( counter = 0; counter <= 20; counter++ ))
do
	echo "sudo ./xdsdfu -f firmware.bin -r -i $counter"
	cmd="sudo ./xdsdfu  -f firmware.bin -r  -i $counter"
	$cmd
done
