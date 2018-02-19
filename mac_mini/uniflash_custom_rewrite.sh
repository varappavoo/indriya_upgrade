#!/bin/bash
flash_ccxml_file=$1
program=$2
other_params=" -targetOp reset restart run"
command="sudo /home/cirlab/ti/uniflash/uniflash.sh -verbose 1 -ccxml $flash_ccxml_file -program $program $other_params"
echo $command
$command
