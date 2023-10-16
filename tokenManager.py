import xml.etree.ElementTree as ET 
import requests, json, io

class TokenManager:
    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url
        
    def getToken(self):
        headers = {
            'Content-Length': str(len(self.username + self.password)),
            'Content-Type': 'application/json',
            'X-Client': 'QGISSkriv' 
        }
                            
        data = {'username': self.username,
                     'password': self.password
                     }
                
        response = requests.post(self.url, json = data, headers = headers)
        
        # print(response.text)
        
        idToken = ''
        accessToken = ''
        refreshToken = ''
        
        file_stream = io.StringIO(response.text)
        tree = ET.parse(file_stream)
        root = tree.getroot()
        
        for child in root:
            if 'idToken' in child.tag:
                idToken = child.text
                
            elif 'accessToken' in child.tag:
                accessToken = child.text
                
            elif 'refreshToken' in child.tag:
                refreshToken = child.text
    
        returnObj = {
            'idToken': idToken, 
            'accessToken': accessToken, 
            'refreshToken': refreshToken
        }
        
        return returnObj