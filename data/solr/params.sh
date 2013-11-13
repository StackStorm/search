#!/bin/bash
# Solr version 4.x
# All Solr params for solr scripts

# 
# Solr installation, points to directory containing start.jar (typially, example dir)
# For Homebrew: /usr/local/Cellar/solr/4.4.0/libexec/example
# For a manual installation, something lie: /usr/local/solr-4.4.0/example
SOLR_DIR=/usr/local/Cellar/solr/4.4.0/libexec/example

# Directory name, where the solr config and schema
MULTICORE='multicore'

# The default port 8983 is set multicore/solr.xml
# Use to overwrite the default port
PORT=8983

URL_BASE=http://localhost:$PORT/solr