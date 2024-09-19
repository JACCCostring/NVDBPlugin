from PyQt5.QtCore import pyqtSignal, QObject
from qgis.utils import iface

import threading

from nvdbapiV3qgis3 import nvdb2kart, nvdbsok2qgis, url2kart, nvdb2kartListe
from nvdbapiv3 import nvdbFagdata, nvdbVegnett

class NVDBDataPaginator( QObject ):
    #signal when thrad done fetching data
    _done_fetching = pyqtSignal( dict )
    
    def __init__(self, search_object):
        super().__init__()
        
        self.data = None
        self.get_dthread = None
        
        self.search_nvdb_data = search_object
        
        self._done_fetching.connect( self.draw )
    
    def init(self):
        self.get_dthread = threading.Thread(target= self.get_fagdata)
    
    def get_fagdata(self):
        if self.get_dthread:
            print('getting records ...')
            
            self.next_s_obj = self.search_nvdb_data.nesteForekomst()
            
            while self.next_s_obj:
                self._done_fetching.emit( self.next_s_obj )

                self.next_s_obj = self.search_nvdb_data.nesteForekomst()
                
    def start_pagination(self):
        # if self.get_dthread:
        self.get_dthread.start()
        
        print('thread started!')
    
    def draw(self, obj):
        
        print('painting ...')
        
        # nvdbsok2qgis( obj )

        nvdb2kartListe( obj, iface )
        
        print('object painted')
        
        # self.get_dthread.join()
        
    def __del__(self):
        # self.get_dthread.join()
        
        pass
    
    def get_thread(self) -> object:
        return self.get_dthread


def test():            
    search_object = nvdbFagdata( 87 )
    
    search_object.filter( {'kommune': 1106} )
    search_object.filter( {'vegsystemreferanse': 'EV'} )
    
    paginator = NVDBDataPaginator( search_object )
    
    paginator.init()
    
    paginator.start_pagination()
    
    paginator._done_fetching.connect( lambda obj: nvdb2kartListe( obj, iface ) )
    
    # paginator.get_thread().join()

test()