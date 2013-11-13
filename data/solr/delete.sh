#!/bin/bash
# Deletes records from Solr

if [ -z "$1" ]
  then
    echo "usage: ./solr-delete.sh {core} {solr-query}"
    echo "  e.g. ./solr-delete.sh vm *:*  This deletes all records in vm collection" 
    exit -1
fi

source $(dirname $0)/params.sh

echo "Deleting $2 in $1"
curl $URL_BASE/$1/update?stream.body=%3Cdelete%3E%3Cquery%3E$2%3C/query%3E%3C/delete%3E

echo Committing...

#send the commit command to make sure all the changes are flushed and visible
curl $URL_BASE/$1/update?commit=true
echo Check the response for results!