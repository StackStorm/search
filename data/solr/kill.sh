#!/bin/sh
# Stops solr process


PID=`ps -ax | grep -v grep | grep solr.solr.home | awk '{print $1}'`

if [ -z "$PID" ]
  then
  echo "Solr process not found: not running?"
  exit -1
fi

echo "Killing Solr process: pid=$PID"
kill $PID
