import requests, json, io
from .abstractPoster import AbstractPoster #this must be in the same directory as delvisKorriger.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot #its need it for signals, slots and QObjects

import xml.etree.ElementTree as ET #this is already included in .abstractPoster but just in case

class DelvisKorrigering(AbstractPoster, QObject):
    new_endringsset_sent = pyqtSignal(list)
    endringsett_form_done = pyqtSignal()
    
    def __init__(self, token, modified_data, extra):
        super().__init__(token, modified_data)
        QObject.__init__(self) #initializing QObject super class
        
        self.extra = extra #data coming from writeToNVB method and need it
        self.xml_string = None # to form xml template
        self.vegobjekter_after_send = [] #to store important info about vegobjekter endepunkter sent til nvdb
        
    def prepare_post(self):
        start = None
        kanseller = None
        status = None
        fremdrift = None
        
#        getting endpoint url
        endpoint = self.extra['endpoint']
        
#        preparing headers
        header = {
            'X-Client': 'QGIS Skriv',
            'Content-Type': 'application/xml',
            'Authorization': 'Bearer ' + self.token
        }
        
#        sending xml data endringset to NVDB waiting queue
        response = requests.post(endpoint, headers = header, data = self.xml_string)
        
        # print(response.text) #debugin
        
        file_stream = io.StringIO(response.text)
        tree = ET.parse(file_stream)
        root = tree.getroot()
        
        for child in root.findall('.//'):
            for tag, src in child.attrib.items():
                if 'src' in tag:
                    if 'start' in src:
                        start = src
                        
                    if 'src' in tag:
                        if 'kanseller' in src:
                            kanseller = src
                    
                    if 'src' in tag:
                        if 'status' in src:
                            status = src
                    
                    if 'src' in tag:
                        if 'fremdrift' in src:
                            fremdrift = src
                        
        self.tokensBeforePost = {
            'start': start, 
            'kanseller': kanseller, 
            'status': status,
            'fremdrift': fremdrift
        }
        
#        print(self.tokensBeforePost) #debuging

#        now start/send the current data to NVDB
#        only if start endpoint exist
        if self.tokensBeforePost['start']:
            self.startPosting()
        
    def formXMLRequest(self, egenskaper_list):
        root = ET.Element('endringssett')
        root.attrib = {'xmlns': 'http://nvdb.vegvesen.no/apiskriv/domain/changeset/v3'}
        
        nvdb_object_id = str(self.modified_data['nvdbid'])
        version = str(self.modified_data['versjon'])
        nvdb_object_type = str(self.extra['nvdb_object_type'])
        
        datakatalogversjon = ET.SubElement(root, 'datakatalogversjon')
        datakatalogversjon.text = self.extra['datakatalog_version']
        
        ansvarlig = ET.SubElement(root, 'ansvarlig')
        ansvarlig.text = self.extra['username']
        
        delvisKorriger = ET.SubElement(root, 'delvisKorriger')
        vegobjekter = ET.SubElement(delvisKorriger, 'vegobjekter')
        
        vegobjekt = ET.SubElement(vegobjekter, 'vegobjekt')
        vegobjekt.attrib = {'typeId': nvdb_object_type, 'nvdbId': nvdb_object_id, 'versjon': version}
        
        egenskaper = ET.SubElement(vegobjekt, 'egenskaper')
        
        new_egenskap = None
        relations_egenskap = None
        geometri_egenskap_found = False
        
        new_modified_data = {}
        
#        fix egenskaper and values when not valid egenskaper is found
        for k1, v1 in self.modified_data.items():
            for k2, v2 in egenskaper_list.items():
                if k1 == k2:
                    new_modified_data[k2] = v2
        
        for item in root.findall('.//'):
                
            if 'egenskaper' in item.tag:
                
                for egenskap_navn, value in new_modified_data.items():
                        
                    if 'Assosierte' not in egenskap_navn: #avoiding adding objekt relasjoner here
                                                    
                        val = str(self.modified_data[egenskap_navn])
                            
                        if 'NULL' not in val: #if not 'null' value then a valid value
                            if '.' not in val: #if not '.' value then its a valid value
                                
                                if egenskap_navn == 'Geometri, punkt' or egenskap_navn == 'Geometri, linje' or egenskap_navn == 'Geometri, flate':
                                    geometri_egenskap_found = True
                                    
#                                those are the rest of the egenskaper
#                                will only add egenskaper that is not Geometri and assosiasjoner
                                if geometri_egenskap_found == False:

                                    new_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                    new_egenskap.attrib = {'typeId': str(value), 'operasjon': 'oppdater'}
                                    egenskap_value = ET.SubElement(new_egenskap, 'verdi')
                                    egenskap_value.text = str(self.modified_data[egenskap_navn])
                                
                            if 'Geometri' in egenskap_navn: #this is a especial case, when vegobjekter has geometri
                            
                                if egenskap_navn == 'Geometri, punkt' or egenskap_navn == 'Geometri, linje' or egenskap_navn == 'Geometri, flate':
                                        
                                    geometri_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                    geometri_egenskap.attrib = {'typeId': str(value), 'operasjon': 'oppdater'}
                                    geometri_egenskap_child = ET.SubElement(geometri_egenskap, 'geometri')
                                        
                                    srid_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'srid')
                                    srid_child_geometri_egenskap.text = '5973'
                                        
                                    wtk_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'wkt')
                                    wtk_child_geometri_egenskap.text = str(self.extra['geometry_found'])
                                
                                            
#        adding validering element to xml form, request to nvdb must have it
        validering_objekt = ET.SubElement(vegobjekt, 'validering')
        lest_fra_nvdb = ET.SubElement(validering_objekt, 'lestFraNvdb')
        lest_fra_nvdb.text = self.extra['sistmodifisert']

#        adding relasjoner to vegobjekter ------- Note: if vegobjekt has a relation then must add child to request not the other way around
        relations = self.extra['relation']
        
#        relasjoner will only be added if vegobjekt has a relation with another vegobjekt
        if relations: 
            
            relations_egenskap = ET.SubElement(vegobjekt, 'assosiasjoner')
            
            for egenskap_id, objekter in relations.items(): #Note: en assosiasjon for hver datterobjekttype
                relation = ET.SubElement(relations_egenskap, 'assosiasjon')
                relation.attrib = {'typeId': str(egenskap_id), 'operasjon': 'oppdater'}
                
                for objekt_id in objekter:
                    value_relation = ET.SubElement(relation, 'nvdbId')
                    value_relation.text = str(objekt_id)
        
        self.xml_string = ET.tostring(root, encoding='utf-8') #be carefull with the unicode

        # print(self.xml_string) #debugin
        
        self.endringsett_form_done.emit()
        
    def startPosting(self):
        fremdrift = None
        status = None
        endrinsett_id = None
        
#        headers
        header = {
            'X-Client': 'QGIS Post',
            'Content-Type': 'application/xml',
            'Authorization': self.token
        }
        
#        getting endpoint start url
        start_endpoint = self.tokensBeforePost['start']
        
#        posting with start request
        response = requests.post(start_endpoint, headers = header)

        file_stream = io.StringIO(response.text)
        tree = ET.parse(file_stream)
        root = tree.getroot()
        
#        parsing endpoints after sending start request
        for child in root.findall('.//'):
            for tag, src in child.attrib.items():
                if 'src' in tag:
                    if 'fremdrift' in src:
                        fremdrift = src
                        
                    if 'src' in tag:
                        if 'status' in src:
                            status = src
                            
        splitted = fremdrift.split('/')
        splitted = splitted[len(splitted) - 2]
        endrinsett_id = splitted
        
        self.tokensAfterPosting = {
            'current_nvdbid': self.extra['current_nvdbid'],
            'fremdrift': fremdrift, 
            'status': status, 
            'endringsett_id': self.extra['endpoint'] + '/' + endrinsett_id
        }
        
        list_vegobjekter_info = {
            'current_nvdbid': self.tokensAfterPosting['current_nvdbid'],
            'status_after_sent': self.tokensAfterPosting['status'],
            'endringsett_id': self.tokensAfterPosting['endringsett_id'],
            'start_endpunkter': self.tokensBeforePost['start'],
            'token': self.token,
            'vegobjekt_navn': self.extra['objekt_navn']
        }
        
        self.vegobjekter_after_send.append(list_vegobjekter_info)
        
#        emiting signal
        self.new_endringsset_sent.emit(self.vegobjekter_after_send)