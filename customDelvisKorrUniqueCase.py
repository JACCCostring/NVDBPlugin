import xml.etree.ElementTree as ET 

from delvisKorrigering import DelvisKorrigering

class CustomDelvisKorrUniqueCase(DelvisKorrigering):
    def __init__(self, token, data, extra):
        super().__init__(token, data, extra)
        pass

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
        
        
        
        
#testing calling
def testing():
    token = "eyJ0eXAiOiJKV1QiLCJraWQiOiJQVi93YnkvQ0lqQW9RS0U4TWJTQjE2QmFsbkE9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoib3hTMXZSZUNaS2NyYllJT1F4eVZRUSIsInN1YiI6ImFsZWNhcyIsImF1ZGl0VHJhY2tpbmdJZCI6ImYwMDNmZjdkLWQ2M2EtNDg3NC04OWJlLWU1ZTM4NTBiNGNjZi05MTk3MjIwIiwic3VibmFtZSI6ImFsZWNhcyIsImlzcyI6Imh0dHBzOi8vd3d3LnRlc3QudmVndmVzZW4ubm86NDQzL29wZW5hbS9vYXV0aDIvcmVhbG1zL3Jvb3QvcmVhbG1zL0VtcGxveWVlcyIsInRva2VuTmFtZSI6ImlkX3Rva2VuIiwiZ2l2ZW5fbmFtZSI6Ikp1bGlvIEFsZXhhbmRlciIsImF1ZCI6IjE3YjllOWEzLThjZTMtNGQxMS05NGU2LTEwMDRjNmMzMzQwOSIsInVpZCI6ImFsZWNhcyIsImF6cCI6IjE3YjllOWEzLThjZTMtNGQxMS05NGU2LTEwMDRjNmMzMzQwOSIsInN2dnJvbGVzIjpbIm52YT0wX2JydWtlcl9mYWdkYXRhIiwic2J0aWxnLWludGVybj11c2VyIiwicHdkcmVzZXQtaW50ZXJuPXVzZXIiLCJzeW5lcmdpPXN0YW5kYXJkIiwidmVna2FtZXJhPWJpbGRlciIsIm52YT03X3V0dmFsZ19hZG1pbiIsIm9rb2lodWI9a3VuZGVyZWdpc3RyZXJpbmciLCJ0cmFmaWtrbmE9dXNlciIsImdpc2xpbmVpbm5zeW5tYXRyYmFzaXM9dXNlciIsInZyPXJhcHBvcnR3ZWJfbGVzIiwibnZhPTBfYnJ1a2VyX3JhcHBvcnRlciIsImZha3RoaXN0YWRtaW49dXNlciIsImRjdG1maWw9dXNlciIsInRla3N0YXBwPWxlcyIsImJpPW9rX21lZGFyYmVpZGVyIiwiYWt0ZHY9aW5uc3luIiwicDM2MD1hbnNhdHQiLCJudmE9MV9pbm5zeW5fYWRtaW4iLCJlcmtsaW5nPXVzZXIiLCJ2cj1zdnZfaW50ZXJuZSIsInJlc3VsdGF0YmFua2VuPXVzZXIiLCJlcGlpbnRyYT11c2VyIiwiZml4dmdkYXQ9YnJ1a2VyIiwiZ2lzbGluZXdlYm1hdHJpa2tlbD11c2VyIiwiYXBleD11c2VyIiwibWltZWhpc3Rvcmlzaz1hbnNhdHQiLCJudmE9MF9icnVrZXJfaW5uc3luIl0sImF1dGhfdGltZSI6MTcyNDE1NDIzNiwibmFtZSI6Ikp1bGlvIEFsZXhhbmRlciBDYXNhZG8gQ2FzdGlsbG8iLCJyZWFsbSI6Ii9FbXBsb3llZXMiLCJleHAiOjE3MjQxODMwMzYsInRva2VuVHlwZSI6IkpXVFRva2VuIiwiaWF0IjoxNzI0MTU0MjM2LCJmYW1pbHlfbmFtZSI6IkNhc2FkbyBDYXN0aWxsbyIsImVtYWlsIjoiYWxleGFuZGVyLmNhc2Fkb0B2ZWd2ZXNlbi5ubyJ9.B-zAZovNdEai9YBsDxys2fm8BGbxsJUOz-RxJIcyLlkZKIdU7dnWXY9U0igr7lkPUoEIRwav0oRvyAAuJ0aVyoLmHki7TwVTaURvdy0zeU1pK3HlsTLNpDZ3XIt0TfX8eAcfYDIk79dat65ZWy-osKd1FmnBY5TNgrIz1IZAOj5oWfkc_0oXcr4JkXFmThRhBWgMBg0zytns34APTvccAl-QA0_CrYe0tNtBmDsNnQ7HWd-U1aGH4YYGFSrM0Vy43YbORLgq1KCvk5mFvLxzL3eS7PxMLNCrJGoyGYiQeC1jacUS3YSS0L1sjNGJ4Odq_VxbH_Gt95kyiTX4aNMadVRqGvILp7joq4w91xQi2av5O3UmoPjnqhdPYfwskPHKL_Yy--RinjelhkqBbGCzjtuYuxWC8aTCQfLbrAM-Hi1peu65ymDsCe07sFlTFrbw6eD1n66GTSIgWi9z0Wo0aFuUi7x1kktC5erBAKG2o-ONptYl2UOqUaW5b0BHRAkA9CjuGasUctQbiBL9PHZySdITKMHfCqmw6IbzJN7ac6bm1ClyJSEfJaEWWPkrsA5uFwogQjQmeQdZ6gnosfZM4rcdgFF6I-kLCkzJaq33EMfH3Q13tlg-KlmIcd-WNF1KpIQG1TB54gX009HAQDett-MN1DFPeE580egVk9oQ21I"
    
    relation = {
    200028: {'vegobjekter': [893884925, 1009978228], 'operation': 'update', 'nvdbid': ''}, 200027: {'vegobjekter': [893884926], 'operation': 'update', 'nvdbid': ''}}

    extra = {   
                    'nvdb_object_type': '86', 
                    'username': 'username', 
                    'datakatalog_version': '4',
                    'endpoint': 'https://nvdbapiskriv.test.atlas.vegvesen.no/rest/v3/endringssett',
                    'sistmodifisert': '12-05-2003',
                    #'current_nvdbid': '11092244',
                    'relation': relation, #dict
                    #'geometry_found': 'geometry',
                    #'objekt_navn': 'belysningpunkt'
                }
    '''
    egen = {   
                    'nvdb_object_type': '22', 
                    'username': 'username', 
                    'datakatalog_version': '55',
                    'endpoint': 'test',
                    'sistmodifisert': '12-05-2003',
                    'current_nvdbid': '11092244',
                    'relation': 'relation', #dict
                    'geometry_found': 'geometry',
                    'objekt_navn': 'belysningpunkt'
                }
                '''
    
    modified_data = {
    'nvdbid': 2011588,
    'versjon': 4
    }
    
    cust = CustomDelvisKorrUniqueCase(token, modified_data, extra)
    
    cust.new_endringsset_sent.connect(lambda: print('done sending changes to NVDB'))

    cust.endringsett_form_done.connect(cust.prepare_post)
    
    cust.formXMLRequest(active_egenskap=False)
                
    
testing()