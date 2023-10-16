import xml.etree.ElementTree as ET 

class AbstractPoster:
    def __init__(self, token, modified_data):
        self.token = token
        self.modified_data = modified_data

    def post(self):
        pass
    
    def formXMLRequest(self, egenskaper_list):
        pass