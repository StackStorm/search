from search.datasource import session
from search.utils import logUtils
from lxml import etree as ET
import pysolr

LOG = logUtils.get_logger(__name__)

class Inventory:
    def __init__(self, solr_url):
        self.solr_url = solr_url

    def post(self, data):
        try:
            solr = session.get_solr_interface(self.solr_url)
            solr.add(data)
        except:
            LOG.exception('Failed to add to solr.')
            raise

    def delete(self, data_id):
        try:
            solr = session.get_solr_interface(self.solr_url)
            solr.delete(data_id)
        except:
            LOG.exception('Failed to delete from solr.')
            raise

    def put(self, data):
        '''
        Supports partial update of solr.
        '''
        if data is None or len(data) == 0:
            return
        # Update Solr: (Mostly from pysolr.Solr code.)
        # Generate the exact update command in xml -
        #  <add>
        #   <doc>
        #    <field name="id">1</field>
        #    <field name="memory_used" update="set">832</field>
        #   </doc>
        #  </add>
        data_xml = ET.Element('add')
        for doc_update in data: 
            doc_element = ET.Element('doc')
            id_field = ET.Element('field', **{'name':'id'})
            id_field.text = str(doc_update['id'])
            doc_element.append(id_field)
            for field in doc_update['fields']:
                field_xml = ET.Element('field', **{'name':field['name'], 'update':field['command']})
                field_xml.text = str(field['value'])
                doc_element.append(field_xml)
            data_xml.append(doc_element)
        # This returns a bytestring.
        data_xml_str = ET.tostring(data_xml, encoding='utf-8')
        # Convert back to Unicode.
        data_xml_str = pysolr.force_unicode(data_xml_str)
        try:
            solr = session.get_solr_interface(self.solr_url)
            solr._update(data_xml_str)
        except:
            LOG.exception('Failed to add to solr.')
            raise
