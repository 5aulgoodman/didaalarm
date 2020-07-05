#!/bin/bash

PID=`ps -ef |grep scan_house.py |grep -v grep | awk '{print $2}'`
if [ "$PID" == "" ]; then
  /usr/bin/python3 /home/deanazure/didaalarm/didaalarm/scan_house.py
else
  starttime=`ps -o lstart -p $PID|tail -1`
  startstamp=`date +%s -d "$starttime"`
  nowtime=`date`
  nowstamp=`date +%s -d "$nowtime"`
  diff=`expr $nowstamp - $startstamp`
  if [ $diff -ge 18000 ]; then
    kill -9 $PID
    /usr/bin/python3 /home/deanazure/didaalarm/didaalarm/scan_house.py 
  fi
fi
