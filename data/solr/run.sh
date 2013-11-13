#!/bin/bash
# Launches the solr instance

source $(dirname $0)/params.sh

# Get the full path to core: works even script runs from diff pwd
# http://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null

echo Running solr cores from [$SCRIPTPATH/$MULTICORE]
cd $SOLR_DIR && java -server $JAVA_OPTS -Dsolr.solr.home=$SCRIPTPATH/$MULTICORE -Djetty.port=$PORT -jar start.jar

