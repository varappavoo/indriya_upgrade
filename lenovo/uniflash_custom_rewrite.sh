#!/bin/bash
# 64bit OS
flash_ccxml_file=$1
program=$2
other_params=" -targetOp reset restart run"
command="sudo /home/cirlab/flash_sensortag_linux_64/dslite.sh -v -e -c $flash_ccxml_file -f $program"
echo $command
$command
