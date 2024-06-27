from qgis.PyQt import uic
from qgis.utils import iface

import os

#user defined modules
from .nvdbLesWrapper import AreaGeoDataParser

FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'more_window.ui'))

class SourceMoreWindow(BASE_CLASS, FORM_CLASS):
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        
        #tab widget control flags
        self.location_tab_active = False
        self.relation_tab_active = False
        #end of tab widget control flags
        
        #setting default tab index flag according to current index
        self.setup_default_tab_index_flags()
        #end of setting default index flag
        
        self.more_main_tab.currentChanged.connect(self.activate_current_tab) #when current tab changes

    def activate_current_tab(self, index):
        if self.more_main_tab.currentIndex() == 0:
            self.location_tab_active = True
            self.relation_tab_active = False

        else:
            self.relation_tab_active = True
            self.location_tab_active = False

    def action_(self):
        if self.location_tab_active:
            self.relocate_vegobjekter()

        elif self.relation_tab_active:
            self.make_relationship_vegobjekter()

    def relocate_vegobjekter(self):
        # stedfesting code here ...
        pass

    def make_relationship_vegobjekter(self):
        # sammenkobling code here ...
        pass
    
    def feed_data(self, component_type: str = str(), data: dict = {}):
        if component_type == 'relation':
           #relation code here ...
            AreaGeoDataParser.set_env('test') #setting environment before use
            
            possible_relation = AreaGeoDataParser.get_possible_parents(int(data['objekttype']))
            
            print(possible_relation)
            
        if component_type == 'location':
            #location code here ...
            pass
        
    # internal own class methods for inside uses
    def setup_default_tab_index_flags(self):
        if self.more_main_tab.currentIndex() == 0:  # 0 stedfesting tab
            self.location_tab_active = True
            self.relation_tab_active = False

        elif self.more_main_tab.currentIndex() == 1:  # 1 kobling tab
            self.relation_tab_active = True
            self.location_tab_active = False

        else:
            self.relation_tab_active = True
            self.location_tab_active = False
