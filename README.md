Search
======

Search service for OpenStack (a prototype)

## Pre-requisites
* Python (dah!): python 2.7, virtualenv, setuptools, pip
* mysql client - must be installed on the system for mysql-python dependency. On Mac, use homebrew: brew install mysql. On debian, apt-get install libmysqlclient-dev.
* libmxl2 - on Ubuntu/Debian, apt-get install libxml2-dev libxslt1-dev
* Java JRE 1.6 and above, and [Apache Solr 4.x](http://lucene.apache.org/solr/)  (tested with 4.4.0) - detaied instruction [./data/solr/README.md](./data/solr/README.md)
	* All pre-requisites for Ubuntu are captured for Ubuntu in toosl/install-prereqs.sh 


## Set up virtualenv
To setup the virtual-env do the following while in the search root folder.

1. `cd $SEARCH_ROOT`
1. `$virtualenv -p python .venv`         [create a virtual environemnt with defaut python. If -p python is not specified could end up with some random python. We use `$VIRTUAL_ENV_ROOT=.venv`]
1. `$source venv/bin/activate`              
1. `$pip install -q -r requirements.txt`      [install all the requirements specified in requirements.txt]. Once done, it should print `Successfully installed` and a list of packages. 

## Run unittests
  `nosetests -v`

## Enable Nova AMQP notifications
We use the same mechanism as Ceilometer or StackTach, and [asking for the same change](http://docs.openstack.org/developer/ceilometer/install/manual.html#installing-the-compute-agent). The AMQP notifications must be enabled on each compute node.

* Edit `/etc/nova/nova.conf` file, in the DEFAULT section add the line: `notification_driver=nova.openstack.common.notifier.rabbit_notifier`
By default it is disabled or [commented out] See [nova.conf sample](https://github.com/openstack/nova/blob/master/etc/nova/nova.conf.sample) on openstack github.

* Restart nova-compute on each compute node for the config to take effect:

    	sudo stop nova-compute
    	sudo start nova-compute

### Hint for DevStack users
With devstack the typical 'sudo service nova-* restart' does not work.
Running 'sudo ./unstack.sh' followed by 'sudo ./stack.sh' also does not work as it overwrites changes to nova.conf. To restart nova-compute on dev-stack: 

1. attach to the screen that stack.sh has started
1. screen -x stack  Note: `screen -r` works, too: we don't know the difference yet. Quick reference on screen: [http://aperiodic.net/screen/quick_reference](http://aperiodic.net/screen/quick_reference)
1. step into the screen for each service individually by 'ctrl+a #{screen no}' e.g. 'ctrl+a 5'is the nova api. Use `ctrl-a, "` to switch between screens if # double-digit.
1. ctrl + c to stop the service; up arrow and enter to restart
1. ctrl+a, d to leave (detach) the screen session 
1. restarting n-cpu shall enable the notifications.  
  
## Start up the workers
1. If using virtualenv, activate it (`source .venv/bin/activate`)
1. modify `$SEARCH_ROOT/config/config.ini` - adjust to your OpenStack setup
1. modify `$SEARCH_ROOT/config/logging.conf` to adjust the path for logs
1. Configure Solr: modify `$SEARCH_ROOT/data/solr/params.sh` to point to your Solr installation
1. Start Solr:     `./solr-testrun.sh`
If everything Ok, the Solr will be configured and running, ready to go.

    	===============================================
		OK :)
		Solr installed, configured, tested, and running
		Go to http://localhost:8983/solr
		For output: tail -f -20 solr.out
		To shut down: ./kill.sh
		
1. Start the workers:

	    python search/start_workers.py -f ./config/config.ini

