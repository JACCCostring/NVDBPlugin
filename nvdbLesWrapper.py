import requests, json, io

import requests, json, io


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
    def getDatakatalogVersion(self, currentMiljo):
        header = {'X-Client': 'ny klient Les'}
        json_data = None

        if 'Produksjon' in currentMiljo:
            url = 'https://nvdbapiles-v3.atlas.vegvesen.no'

        if 'Akseptansetest' in currentMiljo:
            url = 'https://nvdbapiles-v3.test.atlas.vegvesen.no'

        if 'Utvikling' in currentMiljo:
            url = 'https://nvdbapiles-v3.utv.atlas.vegvesen.no'

        endpoint = url + '/vegobjekttyper/versjon'

        response = requests.get(endpoint, headers=header)

        if response.ok:
            raw_data = response.text
            json_data = json.loads(raw_data)

            return json_data['versjon']

        return 'datakatalog version not found'

    @classmethod
    def get_env(self, version: str = 'v3') -> str:
        currentMiljo = self.env.lower()  # this variable value must be already set, before use with, object.set_env() method
        master_endpoint: str = str()
        
        lesUrl = None
        
        #deciding wich endpoint version
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
    def getSistModifisert(self, type, nvdbid, versjon):
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

'''
class AreaGeoDataParser:
    def __init__(self):
        pass
        
    @classmethod    
    def counties(self):
#        adding some headers 
        header = {'X-Client': 'QGIS NVDB Plugin'}
        response = requests.get(self.env + '/omrader/fylker.json', headers = header)
        data = ''
        if response.status_code:
            data = response.text
            
            parsed = json.loads(data)
            dict = {}
            
            for iteration in parsed:
                dict[iteration['navn']] = iteration['nummer']
                
            return dict
            
    @classmethod    
    def communities(self):
#        adding some headers 
        header = {'X-Client': 'QGIS NVDB Plugin'}
        response = requests.get(self.env + '/omrader/kommuner.json', headers = header)
        data = ''
        if response.status_code:
            data = response.text
            
            parsed = json.loads(data)
            dict = {}
            self.communitiesInCounties = {}
            
            for iteration in parsed:
                dict[iteration['navn']] = iteration['nummer']
                self.communitiesInCounties[iteration['navn']] = iteration['fylke']
                
            return dict
            
    @classmethod
    def fetchAllNvdbObjects(self):
        objectTypesEndPoint = self.env + "/vegobjekttyper.json"

#        adding some headers 
        header = {'X-Client': 'QGIS NVDB Plugin'}        
        response = requests.get(objectTypesEndPoint, headers = header)
        
        data = response.text
        
        parsedData = json.loads(data)
        
        dict = {}
        
        for item in parsedData:
            dict[item['navn']] = item['id']
        
        return dict
        
    @classmethod    
    def egenskaper(self, datakatalogId):
        endpointObjectType = self.env + "/vegobjekttyper/" + str(datakatalogId)
        
#        adding some headers 
        header = {'X-Client': 'QGIS NVDB Plugin'}
        data = requests.get(endpointObjectType, headers = header)
        
        raw = data.text
        parsed = json.loads(raw)

        egenskapType = parsed['egenskapstyper']
        listOfNames = {}
        
        for item in egenskapType:
            listOfNames[item['navn']] = item['id']
                
        return listOfNames
        
    @classmethod
    def especificEgenskaper(self, datakatalogId, egenskapName):
        endpointObjectType = self.env + "/vegobjekttyper/" + str(datakatalogId)

#        adding some headers 
        header = {'X-Client': 'QGIS NVDB Plugin'}
        data = requests.get(endpointObjectType, headers = header)
            
        raw = data.text
            
        parsed = json.loads(raw)
            
        egenskapType = parsed['egenskapstyper']
        listOfEspecificProps = {}
            
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
    def setEnvironmentEndPoint(self, env):
        self.env = env
        print(self.env)

    @classmethod
    def getDatakatalogVersion(self, currentMiljo):
        header = {'X-Client': 'QGIS NVDB Skriv'}
        json_data = None
        
        if 'Produksjon' in currentMiljo:
            url = 'https://nvdbapiles-v3.atlas.vegvesen.no'
        
        if 'Akseptansetest' in currentMiljo:
            url = 'https://nvdbapiles-v3.test.atlas.vegvesen.no'
        
        if 'Utvikling' in currentMiljo:
            url = 'https://nvdbapiles-v3.utv.atlas.vegvesen.no'
            
        endpoint = url + '/vegobjekttyper/versjon'
        
        response = requests.get(endpoint, headers = header)
        
        if response.status_code:
            raw_data = response.text
            json_data = json.loads(raw_data)
                        
            return json_data['versjon']
        
        return 'datakatalog version not found'

    @classmethod
    def getMiljoLesEndpoint(self, miljo):
        currentMiljo = miljo #a combo box with Produksjon, Akseptansetest, Utvikling text
        lesUrl = None
        
        if 'Produksjon' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.atlas.vegvesen.no'
        
        if 'Akseptansetest' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.test.atlas.vegvesen.no'
        
        if 'Utvikling' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.utv.atlas.vegvesen.no'
        
        return lesUrl

    @classmethod
    def getSistModifisert(self, type, nvdbid, versjon, currentMiljo):
        endpoint = self.getMiljoLesEndpoint(currentMiljo) + '/' + 'vegobjekter' + '/' + str(type) + '/' + str(nvdbid) + '/' + str(versjon)
                
        header = {
            'Content-Type': 'application/xml',
            'X-Client': 'ny klient Skriv'
        }
        
        response = requests.get(endpoint, headers = header)
        
        json_data = json.loads(response.text)
        
        for data in json_data:
            if data == 'metadata':
                for key, value in json_data[data].items():
                    if key == 'sist_modifisert':
                        return value
'''