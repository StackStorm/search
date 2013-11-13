import sqlalchemy
import pysolr

class DBInfo:
    '''
    Information about the nova controller DB.
    '''
    def __init__(self, host, port, creds):
        self.host = host
        self.port = port
        self.creds = creds

_NOVA_ENGINE = None
_KEYSTONE_ENGINE = None
_GLANCE_ENGINE = None
_SOLR_INTERFACES = None

def get_engine(db_info):
    """Return a SQLAlchemy connection to nova."""
    global _NOVA_ENGINE
    if _NOVA_ENGINE is None:
        db_address = db_info.host + ':' + db_info.port
        novadb_connection_string = 'mysql' +'://'+ db_info.creds +'@'+ db_address +'/nova'
        _NOVA_ENGINE = sqlalchemy.create_engine(novadb_connection_string)
    return _NOVA_ENGINE

def get_keystone_engine(db_info):
    """Return a SQLAlchemy connection to keystone."""
    global _KEYSTONE_ENGINE
    if _KEYSTONE_ENGINE is None:
        db_address = db_info.host + ':' + db_info.port
        novadb_connection_string = 'mysql' +'://'+ db_info.creds +'@'+ db_address +'/keystone'
        _KEYSTONE_ENGINE = sqlalchemy.create_engine(novadb_connection_string)
    return _KEYSTONE_ENGINE

def get_glance_engine(db_info):
    """Return a SQLAlchemy connection to glance."""
    global _GLANCE_ENGINE
    if _GLANCE_ENGINE is None:
        db_address = db_info.host + ':' + db_info.port
        novadb_connection_string = 'mysql' +'://'+ db_info.creds +'@'+ db_address +'/glance'
        _GLANCE_ENGINE = sqlalchemy.create_engine(novadb_connection_string)
    return _GLANCE_ENGINE

def get_solr_interface(solr_url):
    """Returns sunburnt.SolrInterface"""
    global _SOLR_INTERFACES
    if _SOLR_INTERFACES is None:
        _SOLR_INTERFACES = {}
    if (solr_url not in _SOLR_INTERFACES):
        _SOLR_INTERFACES[solr_url] = pysolr.Solr(solr_url)
    return _SOLR_INTERFACES[solr_url]
        