import io
import json
import requests

class AreaGeoDataParser:
    def __init__(self):
        pass

    @classmethod
    def counties(self) -> dict:
        #        adding some headers
        dict = {}
        data = ''
        header = {'X-Client': 'ny klient Les'}
        response = requests.get(self.get_env() + '/omrader/fylker.json?srid=5973', headers=header)

        if response.ok:
            data = response.text

            parsed = json.loads(data)
            dict = {}

            for iteration in parsed:
                dict[iteration['navn']] = iteration['nummer']

            return dict

    @classmethod
    def communities(self) -> dict:
        #        adding some headers
        dict = {}
        data = ''
        header = {'X-Client': 'ny klient Les'}
        response = requests.get(self.get_env() + '/omrader/kommuner.json?srid=5973', headers=header)

        if response.ok:
            data = response.text
            

            parsed = json.loads(data)

            self.communitiesInCounties = {}

            for iteration in parsed:
                dict[iteration['navn']] = iteration['nummer']
                self.communitiesInCounties[iteration['navn']] = iteration['fylke']

            return dict

    @classmethod
    def fetchAllNvdbObjects(self) -> dict:
        dict = {}
        objectTypesEndPoint = self.get_env() + "/vegobjekttyper.json"

        #        adding some headers
        header = {'X-Client': 'ny klient Les'}
        response = requests.get(objectTypesEndPoint, headers=header)

        if response.ok:
            data = response.text

            parsedData = json.loads(data)

            for item in parsedData:
                dict[item['navn']] = item['id']

        return dict

    @classmethod
    def egenskaper(self, datakatalogId: int) -> dict:
        listOfNames = {}
        endpointObjectType = self.get_env() + "/vegobjekttyper/" + str(datakatalogId)

        #        adding some headers
        header = {'X-Client': 'ny klient Les'}
        data = requests.get(endpointObjectType, headers=header)

        if data.ok:
            raw = data.text
            parsed = json.loads(raw)

            egenskapType = parsed['egenskapstyper']

            for item in egenskapType:
                listOfNames[item['navn']] = item['id']

        return listOfNames

    @classmethod
    def especificEgenskaper(self, datakatalogId, egenskapName) -> dict:
        listOfEspecificProps = {}
        endpointObjectType = self.get_env() + "/vegobjekttyper/" + str(datakatalogId)

        #        adding some headers
        header = {'X-Client': 'ny klient Les'}
        data = requests.get(endpointObjectType, headers=header)

        if data.ok:
            raw = data.text

            parsed = json.loads(raw)

            egenskapType = parsed['egenskapstyper']

            for item in egenskapType:
                if item['navn'] == egenskapName:
                    for name, props in item.items():
                        if name == 'datatype':
                            self.especificEgenskapDataType = props

                        if name == 'tillatte_verdier':
                            for especificProp in props:
                                listOfEspecificProps[especificProp['verdi']] = especificProp['id']

        return listOfEspecificProps

    @classmethod
    def egenskapDataType(self):
        return self.especificEgenskapDataType

    @classmethod
    def set_env(self, env: str) -> None:
        self.env = env

    @classmethod
    def get_possible_parents(self, type: int = 0) -> list:
        road_objects_possible_parents: list = []

        endpoint = self.get_env() + '/' + 'vegobjekttyper' + '/' + str(type)
        header = {
            'ContentType': 'application/json',
            'X-Client': 'ny klient Les'
        }
        params = {'inkluder': 'relasjonstyper'}
        
        response = requests.get(endpoint, headers=header, params=params)
        
        relationtype = None
        
        if response.ok:
            for in_content in response.json():
                if in_content == 'relasjonstyper':
                    relationtype = response.json()[in_content]
        try:
            if relationtype:
                foreldre = relationtype['foreldre']
                
                for object_type in foreldre:
                    for items, value_items in object_type.items():
                        if items == 'innhold':
                            # type_field = object_type[items]['type']['navn']
                            
                            type_object_id = object_type[items]['type']['id']
                            type_object_name = object_type[items]['type']['navn']
                            
                            form_dict_type = {'id': type_object_id, 'name': type_object_name}
                            
                            # clear any element different then id or name elements
                            road_objects_possible_parents.append(form_dict_type)

        except:
            pass
            
        return road_objects_possible_parents
        
    @classmethod
    def get_children_relation_from_parent(self, p_type: int = int(), p_nvdbid: int = int()):
        endpoint = self.get_env() + '/' + 'vegobjekter' + '/' + str(p_type) + '/' + str(p_nvdbid)
        
        header = {
            'ContentType': 'application/json',
            'X-Client': 'ny klient Les'
        }
        
        params = {'inkluder': 'relasjoner'}

        response = requests.get(endpoint, headers=header, params=params)
        
        list_of_roadobjects: list = []
        plugin_dict: dict = {}
        list_id: dict = {}
        
        if response.ok:

            response_plugin = json.loads(response.text)

            try:
                
                list_of_roadobjects = response_plugin["relasjoner"]["barn"][0]["vegobjekter"]

                # getting the object_id of the child objects
                list_id = response_plugin["relasjoner"]["barn"][0]["id"]
                
            except KeyError:
                #no child object, then just return
                return

            # create a dict with the data put together
            plugin_dict = {list_id: {"vegobjekter": list_of_roadobjects}}

            """# CASE OF SWAGGER OUTPUT

                        print(response.text)
                        response_swagger = json.loads(response.text)

                        # getting length of the list containing the child objects
                        length_vegobjekter = len(response_swagger["relasjoner"]["barn"][0]["vegobjekter"])

                        # list to contain child objects
                        list_of_roadobjects = []

                        for i in range(0, length_vegobjekter):
                            # adding each child object to the list
                            list_of_roadobjects.append(response_swagger["relasjoner"]["barn"][0]["vegobjekter"][i]["id"])

                        # getting the object_id of the child objects
                        list_id = [response_swagger["relasjoner"]["barn"][0]["id"]]

                        # create a dict with the data put together
                        swagger_dict = {list_id: {"vegobjekter": list_of_roadobjects}}
                        print(swagger_dict)
            """
            
            return plugin_dict

        
    @classmethod
    def get_datacatalog_relation_type(self, object_type_id: int = int(), type_name: str = str()) -> int:
        endpoint = self.get_env(version = 'v4') + '/datakatalog/api/v1/vegobjekttyper/' + str(object_type_id)
    
        header = {
            'ContentType': 'application/json',
            'X-Client': 'ny klient Les'
        }
        
        params = {'inkluder': 'relasjonstyper'}
        
        response = requests.get(endpoint, headers=header, params=params)

        if response.ok:
            resp_json = json.loads(response.text)
            
            for child in resp_json['relasjonstyper']['barn']:
                print(f"Child: {child['innhold']['type']['navn']}")
                if child['innhold']['type']['navn'] == type_name:
                    print("Found!")
                    return child['innhold']['id']
        
        return 0

    @classmethod
    def get_last_version(self, p_nvdbid: int = int(), p_type_id: int = int()):
        endpoint = self.get_env() + '/' + 'vegobjekter' + '/' + str(p_type_id) + '/' + str(p_nvdbid)

        header = {
            'ContentType': 'application/json',
            'X-Client': 'ny klient Les'
        }

        params = {'inkluder': 'metadata'}

        response = requests.get(endpoint, headers=header, params=params)
        version: int = int()

        if response.ok:
            data = json.loads(response.text)

            metadata = data['metadata']
            version = metadata['versjon']

            return version

    @classmethod
    def get_env(self, version: str = 'v3') -> str:
        currentMiljo = self.env.lower()  # this variable value must be already set, before use with, object.set_env() method
        master_endpoint: str = str()

        lesUrl = None

        # deciding wich endpoint version
        if version == 'v3':
            master_endpoint = 'https://nvdbapiles-v3.'

        elif version == 'v4':
            master_endpoint = 'https://nvdbapiles.'

        if 'prod' or 'Produksjon' in currentMiljo:
            lesUrl = master_endpoint + 'atlas.vegvesen.no'

        if 'test' in currentMiljo:
            lesUrl = master_endpoint + 'test.atlas.vegvesen.no'

        if 'utv' in currentMiljo:
            lesUrl = master_endpoint + 'utv.atlas.vegvesen.no'

        return lesUrl

    @classmethod
    def get_datacatalog_version(self, currentMiljo):
        header = {'X-Client': 'QGIS NVDB Skriv'}
        json_data = None

        if 'Produksjon' in currentMiljo:
            url = 'https://nvdbapiles-v3.atlas.vegvesen.no'

        if 'Akseptansetest' in currentMiljo:
            url = 'https://nvdbapiles-v3.test.atlas.vegvesen.no'

        if 'Utvikling' in currentMiljo:
            url = 'https://nvdbapiles-v3.utv.atlas.vegvesen.no'

        endpoint = url + '/vegobjekttyper/versjon'

        response = requests.get(endpoint, headers=header)

        if response.status_code:
            raw_data = response.text
            json_data = json.loads(raw_data)

            return json_data['versjon']

        return 'datakatalog version not found'

    @classmethod
    def get_last_time_modified(self, type, nvdbid, versjon):
        endpoint = self.get_env() + '/' + 'vegobjekter' + '/' + str(type) + '/' + str(
            nvdbid) + '/' + str(versjon)

        header = {
            'Content-Type': 'application/xml',
            'X-Client': 'ny klient Les'
        }

        response = requests.get(endpoint, headers=header)

        json_data = json.loads(response.text)

        for data in json_data:
            if data == 'metadata':
                for key, value in json_data[data].items():
                    if key == 'sist_modifisert':
                        return value

        # return appended_parents