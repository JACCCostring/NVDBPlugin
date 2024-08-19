from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot #its need it for signals, slots and QObjects

from .abstractPoster import AbstractPoster #this must be in the same directory as delvisKorriger.py

import xml.etree.ElementTree as ET #this is already included in .abstractPoster but just in case

import requests, json, io

class DelvisKorrigering(AbstractPoster, QObject):
    new_endringsset_sent = pyqtSignal(list)
    endringsett_form_done = pyqtSignal()
    response_error = pyqtSignal(str)
    response_success = pyqtSignal(str)


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
#remember xml_string variable is comming from formXMLRequest method
        response = requests.post(endpoint, headers = header, data = self.xml_string)
        #print("Delviskorrigering reponse: ")
        #print(response.text) #debugin

        if response.ok != True:

            self.parseXml_prepare_method(response.text)
            #print(response.text) # Error: Gir ikke beskjed når bruker ikke har tilgang
            return


        if response.ok:
            successful = "Status: OK"
            self.response_success.emit(successful)

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
            
            print('prepare post: ', self.tokensBeforePost['status'])
            
    #        print(self.tokensBeforePost) #debuging

    #        now start/send the current data to NVDB
    #        only if start endpoint exist
            if self.tokensBeforePost['start']:
                self.startPosting()


    def parseXml_prepare_method(self, xml_text):
        # Parse the XML content
        root = ET.fromstring(xml_text)

        # Defining the namespace input
        ns = {'fault' :'http://nvdb.vegvesen.no/apiskriv/fault/v1'}

        # Finding the message element and getting its text
        msg = root.find('.//fault:message', ns)

        if msg is not None:
            # Sending message using a signal to display to user
            self.response_error.emit(msg.text)

        else:
            print("Message element not found")


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
        
        #fix egenskaper and values when not valid egenskaper is found
        for k1, v1 in self.modified_data.items():
            for k2, v2 in egenskaper_list.items():
                if k1 == k2:
                    new_modified_data[k2] = v2
        
        for item in root.findall('.//'):
                
            if 'egenskaper' in item.tag:
                
                for egenskap_navn, value in new_modified_data.items():
                    # print(egenskap_navn, ': ', self.modified_data[egenskap_navn])
                        
                    if 'Assosierte' not in egenskap_navn: #avoiding adding objekt relasjoner here
                                                    
                        val = str(self.modified_data[egenskap_navn])
                        # val = str(new_modified_data[egenskap_navn])
                        
                        if 'NULL' not in val: #if not 'null' value then a valid value
                        
                            '''
                            here we having a logic issue about '.', because if for example val = decimal point number ex: 11.00000
                            then val will get lose because we are comparing if val is '.', but if we wanna make sure wether val is a value number or not
                            we need to try a int conversion and if raise an exception so we know now val is a '.' and not a number
                            '''
                            
                            if val != '.': #if not '.' value then its a valid value
                                
                                if egenskap_navn == 'Geometri, punkt' or egenskap_navn == 'Geometri, linje' or egenskap_navn == 'Geometri, flate':
                                    geometri_egenskap_found = True
                                    
                                '''
                                those are the rest of the egenskaper
                                will only add egenskaper that is not Geometri and assosiasjoner
                                '''
                                if geometri_egenskap_found == False:
                                    '''
                                    operation will depend on if value is 'N/A' or not
                                    if 'N/A' then we delete egenskap and if not then update egenskap
                                    '''
                                    operation = 'slett' if self.modified_data[egenskap_navn] == 'N/A' else 'oppdater'
                                    # operation = 'slett' if new_modified_data[egenskap_navn] == 'N/A' else 'oppdater'
                                        
                                    # print(operation) #debug
                                    # print(egenskap_navn, ': ', self.modified_data[egenskap_navn])
                                            
                                    new_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                    new_egenskap.attrib = {'typeId': str(value), 'operasjon': operation}
                                            
                                        #debug
                                        # print(egenskap_navn, ': ', val, ' type ', type(val))
                                            
                                    if operation == 'oppdater':
                                        egenskap_value = ET.SubElement(new_egenskap, 'verdi')
                                        egenskap_value.text = str(self.modified_data[egenskap_navn])
                                            # egenskap_value.text = str(new_modified_data[egenskap_navn])
                                
                            if 'Geometri' in egenskap_navn: #this is a especial case, when vegobjekter has geometri
                            
                                if egenskap_navn == 'Geometri, punkt' or egenskap_navn == 'Geometri, linje' or egenskap_navn == 'Geometri, flate':
                                        
                                    geometri_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                    geometri_egenskap.attrib = {'typeId': str(value), 'operasjon': 'oppdater'}
                                    geometri_egenskap_child = ET.SubElement(geometri_egenskap, 'geometri')
                                        
                                    srid_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'srid')
                                    srid_child_geometri_egenskap.text = '5973'
                                        
                                    wtk_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'wkt')
                                    wtk_child_geometri_egenskap.text = str(self.extra['geometry_found'])
                                
                                            
        #adding Validering to XML endringsett
        validering_objekt = ET.SubElement(vegobjekt, 'validering')
        lest_fra_nvdb = ET.SubElement(validering_objekt, 'lestFraNvdb')
        lest_fra_nvdb.text = self.extra['sistmodifisert']

        '''
        adding relations to the parent road object
        
        Note: when adding relation to a road object, convention is that
        parent object must add child as a relation to it and not the other way around.
        '''
        relations = self.extra['relation']

        if relations: 
            
            relations_egenskap = ET.SubElement(vegobjekt, 'assosiasjoner')
            
            for enum_catalog_type_nvdb, item in relations.items():
                #Note: for each relation or assosiasjon a sub or new assosiasjon must be added individual if need it.
                relation = ET.SubElement(relations_egenskap, 'assosiasjon')
                relation.attrib = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}
                
                '''
                    find child road object marked for removing, road object tagged name is
                    remove_nvdbid and it's existing already there from nvdb_beta_dialog.py module
                    from here we need to make sure that:
                    
                    if operation is Remove then:
                    -remove case happens (remove child object relation)
                    
                    if operation is default (update) then:
                    -update case happens (update child object relation)
                    
                    if operation is new then:
                    -new case happens (add new child object relation)
                    
                    Documentation to fallow NVDB API convention: https://nvdb.atlas.vegvesen.no/docs/produkter/nvdbapis/endringssett/Oppbygging/#om-assosiasjoner
                '''
                
                '''
                #Remove Case
                if item['operation'] == 'remove':
                    
                    sub_remove_relation = ET.SubElement(relation, 'nvdbId')
                    sub_remove_relation.attrib = { 'operasjon':  "slett" }

                    for enum_catalog_type_nvdb_sub, item_sub in relations.items():
                        #for now this loop do not make any effect on the changes, but a bad form xml will be generated
                        #and is ok for now, to avoid this uncomment sub_relation.text = str(item['remove_nvdbid'])
    
                        print('enum_catalog_type_nvdb: ', enum_catalog_type_nvdb_sub, 'road objects: ', item_sub['nvdbid'])
                        # sub_remove_relation.text = str(item_sub['nvdbid']) #commented for now, but need it later for removing child relationship
                
                '''
                
                #Add New Case
                if item['operation'] == 'add':
                    
                    sub_add_relation = ET.SubElement(relation, 'nvdbId')
                    sub_add_relation.attrib = { 'operasjon': 'ny' }
                    
                    for enum_catalog_type_nvdb_sub_rm, item_sub_rm in relations.items():
                        print('enum catalog: ', enum_catalog_nvdb_sub_rm, 'items: ', item_sub_rm['nvdbid'])
                
            
                #Update Case and Default Case
                if item['operation'] == 'update':
                    # relation = ET.SubElement = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}
                    relation.attrib = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}

                    #and if it's an update, then add road objects as child
                    for nvdbid in item['vegobjekter']:
                        value_relation = ET.SubElement(relation, 'nvdbId')
                        value_relation.text = str(nvdbid)
        
        self.xml_string = ET.tostring(root, encoding='utf-8') #be carefull with the unicode

        print(self.xml_string) #debuging info of hole formed XML endingsett
        
        # emiting signal
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
        
        print('posting: ', list_vegobjekter_info['status_after_sent'])
        
        self.vegobjekter_after_send.append(list_vegobjekter_info)
        
        #        emiting signal
        self.new_endringsset_sent.emit(self.vegobjekter_after_send)