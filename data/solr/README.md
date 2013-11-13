#SOLR for OpenStack Search

Per current design and understanding of solr we are setting up solr to store each document type in a separate core. This effectively denormalizes the data, allows us to maintain separate indexes effectively and maintain some sanity in each schema. To meet this end do the following in the solr instance :

## Install Solr
1. On Mac, use [homebrew](http://brew.sh) : `brew  install solr`
1. Or, install [Solr](http://lucene.apache.org/solr/) into $SOLR_DIR directory (e.g., /usr/local/solr-4.4.0), and update the `params.sh` 
to point to the directory under solr containing start.jar (e.g., /usr/local/solr-4.4.0/example)
1. Start Solr:
		
		$ cd search/data/solr
		$ ./run.sh

1. Open admin console [http://localhost:8983/solr/](http://localhost:8983/solr/), verify that 2 cores are seen there.

1. Post some data, check that you can see them in admin console

		$ ./post vm multicore/_sampledocs/vms.json
		$ ./post host multicore/_sampledocs/hosts.json
		
1. To stop, `./kill.sh`. To start, `./run.sh` To add test document, `./post.sh vm multicore/_sampledocs/vms.json`. To delete, `./solr-delete vm *:*`

##Run test script
**NOTE: THIS DELETES ALL DATA**
The script kills Solr process if already started, deploys schemas to host and vm, deletes the data, and tests the configuration with the test data.

    ./solr-testrun.sh
If everything Ok, the Solr will be configured and running, ready to go.

    ===============================================
	OK :)
	Solr installed, configured, tested, and running
	Go to http://localhost:8983/solr
	For output: tail -f -20 solr.out
	To shut down: ./kill.sh


## Working with Solr
1. Add cores under ```./multicore/```. Keep sample documents under multicore/_sampledocs; name them as plural of core (e.g vms.json for vm).   
1. Keep the scripts updated with the changes; test everything by running the ```solr-test.sh```



