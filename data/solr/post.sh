#!/bin/sh
# Posts a JSON files to solr.
# try schema/vms.json

if [ -z "$2" ]
  then
    echo "usage: ./solr-post.sh {core} {file.json}"
    echo "  e.g. ./solr-post.sh schema/vms.json"
    exit -1
fi
. $(dirname $0)/params.sh

echo Posting file $f to $URL_BASE/$1
curl $URL_BASE/$1/update --data-binary @$2 -H 'Content-type:application/json'
echo

#send the commit command to make sure all the changes are flushed and visible
curl $URL_BASE/$1/update?commit=true 
echo
