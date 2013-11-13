# Osh pre-requirements for Debian/Ubuntu
# Tested on Ubuntu 12.04

# Node JS and NPM
sudo apt-get -y update
sudo apt-get -y install python-software-properties python g++ make

# Java
sudo apt-get -y install openjdk-7-jre
java -version

### Install libvirt, libxml mysql client, curl, python, git
sudo apt-get install -y libxml2-dev libxslt1-dev
sudo apt-get install -y libmysqlclient-dev
sudo apt-get install -y curl
sudo apt-get install -y python-dev python-pip python-virtualenv
sudo apt-get install -y git

# Solr
curl http://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz | tar xz
# Place Solr in a goodlocation, e.g. /usr//usr/local/solr-4.4.0

  