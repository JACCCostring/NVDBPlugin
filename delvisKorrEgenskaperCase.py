from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot  # its need it for signals, slots and QObjects

import xml.etree.ElementTree as ET

import requests, json, io


class DelvisKorrEgenskaperCase(QObject):
    
    new_endringsset_sent = pyqtSignal(dict)
    endringsett_form_done = pyqtSignal()
    
    onEndringsett_fail = pyqtSignal(int, bool, str)
    
#new changes for Senay

    def __init__(self, token, modified_data, extra):
        QObject.__init__(self)  # initializing QObject super class
        '''
        decided not to inherit or have any abstract depending class

        not need it, therefore we opt for subclassing this class, to especialize
        another class and just override methods instead
        '''
        self.modified_data = modified_data  # new
        self.token = token  # new

        self.extra = extra  # data coming from writeToNVB method and need it
        self.xml_string = None  # to form xml template

    def formXMLRequest(self, egenskaper_list, active_egenskap=True):
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

        '''
        from here egenskaper will be parse, so it's up to the developer when subclassing
        to control this part here, turning to True or False the active_egenskap flag, when
        instantiating/creating the class
        '''
        if active_egenskap:
            egenskaper = ET.SubElement(vegobjekt, 'egenskaper')

            new_egenskap = None
            relations_egenskap = None
            geometri_egenskap_found = False

            new_modified_data = {}

            # fix egenskaper and values when not valid egenskaper is found
            for k1, v1 in self.modified_data.items():
                for k2, v2 in egenskaper_list.items():
                    if k1 == k2:
                        new_modified_data[k2] = v2

            for item in root.findall('.//'):

                if 'egenskaper' in item.tag:

                    for egenskap_navn, value in new_modified_data.items():
                        # print(egenskap_navn, ': ', self.modified_data[egenskap_navn])

                        if 'Assosierte' not in egenskap_navn:  # avoiding adding objekt relasjoner here

                            val = str(self.modified_data[egenskap_navn])
                            # val = str(new_modified_data[egenskap_navn])

                            if 'NULL' not in val:  # if not 'null' value then a valid value

                                '''
                                here we having a logic issue about '.', because if for example val = decimal point number ex: 11.00000
                                then val will get lose because we are comparing if val is '.', but if we wanna make sure wether val is a value number or not
                                we need to try a int conversion and if raise an exception so we know now val is a '.' and not a number
                                '''

                                if val != '.':  # if not '.' value then its a valid value

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

                                        new_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                        new_egenskap.attrib = {'typeId': str(value), 'operasjon': operation}
                                        
                                        # print('=====>', egenskap_navn, ': ', value, ':', self.modified_data[egenskap_navn])

                                        if operation == 'oppdater':
                                            egenskap_value = ET.SubElement(new_egenskap, 'verdi')
                                            egenskap_value.text = str(self.modified_data[egenskap_navn])

                                if 'Geometri' in egenskap_navn:  # this is a especial case, when vegobjekter has geometri

                                    if egenskap_navn == 'Geometri, punkt' or egenskap_navn == 'Geometri, linje' or egenskap_navn == 'Geometri, flate':
                                        geometri_egenskap = ET.SubElement(egenskaper, 'egenskap')
                                        geometri_egenskap.attrib = {'typeId': str(value), 'operasjon': 'oppdater'}
                                        geometri_egenskap_child = ET.SubElement(geometri_egenskap, 'geometri')

                                        srid_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'srid')
                                        srid_child_geometri_egenskap.text = '5973'

                                        wtk_child_geometri_egenskap = ET.SubElement(geometri_egenskap_child, 'wkt')
                                        wtk_child_geometri_egenskap.text = str(self.extra['geometry_found'])

        # adding Validering to XML endringsett
        validering_objekt = ET.SubElement(vegobjekt, 'validering')
        lest_fra_nvdb = ET.SubElement(validering_objekt, 'lestFraNvdb')
        lest_fra_nvdb.text = self.extra['sistmodifisert']

        '''
        adding relations to the parent road object

        Note: when adding relation to a road object, convention is that
        parent object must add child as a relation to it and not the other way around.
        '''
        
        '''
        relations = self.extra['relation']

        if relations:

            relations_egenskap = ET.SubElement(vegobjekt, 'assosiasjoner')

            for enum_catalog_type_nvdb, item in relations.items():
                # Note: for each relation or assosiasjon a sub or new assosiasjon must be added individual if need it.
                relation = ET.SubElement(relations_egenskap, 'assosiasjon')
                relation.attrib = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}


                #Default relation Case
                if item['operation'] == 'update':
                    relation.attrib = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}

                    # and if it's an update, then add road objects as child
                    for nvdbid in item['vegobjekter']:
                        value_relation = ET.SubElement(relation, 'nvdbId')
                        value_relation.text = str(nvdbid)
        '''
        
        self.xml_string = ET.tostring(root, encoding='utf-8')  # be carefull with the unicode

        # print(self.xml_string)  # debuging info of hole formed XML endingsett

        # emiting signal
        self.endringsett_form_done.emit()


    def prepare_post(self):
        start = None
        kanseller = None
        status = None
        fremdrift = None

        # getting endpoint url
        endpoint = self.extra['endpoint']

        # preparing headers
        header = {
            'X-Client': 'QGIS Skriv',
            'Content-Type': 'application/xml',
            'Authorization': 'Bearer ' + self.token
        }

        '''
        sending xml data endringset to NVDB waiting queue
        remember xml_string variable is comming from formXMLRequest method
        '''
        response = requests.post(endpoint, headers=header, data=self.xml_string)

        if not response.ok:
            
            #emiting signal to comunicate with table widget in skriv window module
            self.onEndringsett_fail.emit(int(self.extra['current_nvdbid']), False, response.text)
            
            # return
        
        if response.ok:
            
            file_stream = io.StringIO(response.text)
            
            try:
                
                tree = ET.parse(file_stream)
                
            except ET.ParseError:
                
                #emiting to comunicate something went wrong when preparing post
                self.onEndringsett_fail.emit(int(self.extra['current_nvdbid']), False, response.text)
                return
                
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

            '''
            now start/send the current data to NVDB
            only if start endpoint exist
            '''
            if self.tokensBeforePost['start']:                
                #emiting signal to comunicate with table widget in skriv window module
                self.onEndringsett_fail.emit(int(self.extra['current_nvdbid']), True, 'utført og startet')
                
                self.startPosting()

    def startPosting(self):
        fremdrift = None
        status = None
        endrinsett_id = None

        # headers
        header = {
            'X-Client': 'QGIS Post',
            'Content-Type': 'application/xml',
            'Authorization': self.token
        }
        
        # getting endpoint start url
        start_endpoint = self.tokensBeforePost['start']

        # posting with start request
        response = requests.post(start_endpoint, headers=header)
        
        if not response.ok:
            pass

        if response.ok:
            
            file_stream = io.StringIO(response.text)
            
            try:
                tree = ET.parse(file_stream)
                
            except ET.ParseError:
                #emiting signal to comunicate with table widget in skriv window module
                self.onEndringsett_fail.emit(int(self.extra['current_nvdbid']), False, response.text)
                return
                
            root = tree.getroot()

            # parsing endpoints after sending start request
            for child in root.findall('.//'):
                for tag, src in child.attrib.items():
                    if 'src' in tag:
                        if 'fremdrift' in src:
                            fremdrift = src

                        if 'src' in tag:
                            if 'status' in src:
                                status = src

            try:
                
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

                # emiting signal
                self.new_endringsset_sent.emit(list_vegobjekter_info)
                
            except AttributeError:
                pass