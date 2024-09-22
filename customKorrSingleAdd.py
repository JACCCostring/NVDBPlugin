import xml.etree.ElementTree as ET 

from .delvisKorrEgenskaperCase import DelvisKorrEgenskaperCase

class CustomDelvisKorrSingleAdd(DelvisKorrEgenskaperCase):
    def __init__(self, token, data, extra):
        super().__init__(token, data, extra)
        pass
    
    #override
    def formXMLRequest(self, active_egenskap=True):
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
        
        '''
        if relations variable is populated, means that we need to add all the relation
        plus the one selected from QGIS kart.
        '''
        if relations and self.extra['hasAnyRelation']:
            print('hasAnyRelation == True')
            relations_egenskap = ET.SubElement(vegobjekt, 'assosiasjoner')
            
            for enum_catalog_type_nvdb, item in relations.items():
                '''
                Note:
                        for each relation or assosiasjon a sub or new assosiasjon must be added individual if need it.
                '''
                relation = ET.SubElement(relations_egenskap, 'assosiasjon')
                relation.attrib = {'typeId': str(enum_catalog_type_nvdb), 'operasjon': 'oppdater'}
                
                sub_remove_relation = ET.SubElement(relation, 'nvdbId')
                sub_remove_relation.attrib = { 'operasjon':  "ny" }

                sub_remove_relation.text = str( self.extra['add_child_nvdbid'] )
        
        '''
        if not relation is found, means that we can not add any relatio from relations variable
        and we must add the only child road object selected from QGIS kart.
        '''
        if not self.extra['hasAnyRelation']:
            print('hasAnyRelation == False')
            relations_egenskap = ET.SubElement(vegobjekt, 'assosiasjoner')
            
            relation = ET.SubElement(relations_egenskap, 'assosiasjon')
            relation.attrib = {'typeId': str(self.extra['datacatalog_enumId']), 'operasjon': 'oppdater'}
            
            sub_remove_relation = ET.SubElement(relation, 'nvdbId')
            sub_remove_relation.attrib = { 'operasjon':  "ny" }

            sub_remove_relation.text = str( self.extra['add_child_nvdbid'] )
            
        self.xml_string = ET.tostring(root, encoding='utf-8') #be carefull with the unicode

        print(self.xml_string) #debuging info of hole formed XML endingsett
        
        # emiting signal
        self.endringsett_form_done.emit()