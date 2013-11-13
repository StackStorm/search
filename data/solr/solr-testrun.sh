#!/bin/bash
# Testing Solr installation and configuration and running the instance.
#
# This script will launche Solr (restarting if already running); clean it out 
# (delete all documents), deploy schema, test it with sample doc, 
# and clean it up again, keeping solr running (background of foreground)
# DANGER: THIS DELETES ALL THE SOLR RECORDS!

BASE_DIR=`dirname $0`
source $BASE_DIR/params.sh
SOLR_START_TIME=10

echo "Stopping Solr in case it is already running..."
$BASE_DIR/kill.sh

# The script runs solr in foreground, using the terminal for output.
# To detauch completely, uncomment the line below: nohup $BASE_DIR/solr-run.sh >solr.out 2>&1 &
nohup $BASE_DIR/run.sh >solr.out 2>&1 &


echo Launching Solr and sleeping $SOLR_START_TIME sec to get it started...

sleep $SOLR_START_TIME

echo Deleting vms...
$BASE_DIR/delete.sh vm *:*

echo Deleting hosts...
$BASE_DIR/delete.sh host *:*

echo Testing vm collection...
$BASE_DIR/post.sh vm $BASE_DIR/$MULTICORE/_sampledocs/vms.json

RECORDS=`curl --silent $URL_BASE'/vm/select?q=*%3A*&fl=name&wt=csv&indent=true' | wc -l`
MY_COOL_VM=`curl --silent $URL_BASE'/vm/select?q=*%3A*&fl=name&wt=csv&indent=true' | grep "My Cool VM" | wc -l`
echo $RECORDS - $MY_COOL_VM

$BASE_DIR/delete.sh vm *:*
AFTER_DELETE=`curl --silent $URL_BASE'/vm/select?q=*%3A*&fl=name&wt=csv&indent=true' | wc -l`

echo Testing host collection...
$BASE_DIR/post.sh host $BASE_DIR/$MULTICORE/_sampledocs/hosts.json

HOSTS=`curl --silent $URL_BASE'/host/select?q=*%3A*&fl=name&wt=csv&indent=true' | wc -l`
HOST_1=`curl --silent $URL_BASE'/host/select?q=*%3A*&fl=name&wt=csv&indent=true' | grep "host1" | wc -l`
echo $HOSTS - $HOST_1

$BASE_DIR/delete.sh host *:*
AFTER_HOST_DELETE=`curl --silent $URL_BASE'/host/select?q=*%3A*&fl=name&wt=csv&indent=true' | wc -l`


echo $RECORDS - $MY_COOL_VM -  $AFTER_DELETE
echo $HOSTS - $HOST_1 -  $AFTER_HOST_DELETE

echo ===========================================================================
if [[ $RECORDS -eq 3 && $MY_COOL_VM -eq 1 && $AFTER_DELETE -eq 1 
  &&  $HOSTS -eq 3 && $HOST_1 -eq 1 && AFTER_HOST_DELETE -eq 1 ]]
then
   echo OK ":)"
   echo Solr installed, configured, tested, and running
   echo Go to $URL_BASE
   echo For output: tail -f -20 solr.out
   echo To shut down: ./kill.sh
else
   echo FAILED!
   echo Check your Solr installation and configuration
fi
echo
echo
