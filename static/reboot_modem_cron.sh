#!/bin/sh
# Script to run the modem reboot every <times|4> days

if [[ ! -z "$1" ]]
then
	times=$(($1-1))
else
	times=4
fi

count=/home/ansible/ansible/static/count
time=0
if [[ ! -f $count ]]
then
	echo $time > $count
else
	time=`cat $count`
fi

if [[ $time -ge $times ]]
then
	echo 0 > $count
	/home/ansible/ansible/cmcc_reboot.py
else
	echo $(($time+1)) > $count
fi

