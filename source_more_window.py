# from PyQt5 import QtCore
from qgis.PyQt import uic
from qgis.utils import iface

import os

# import inspect

# from .more_window import Ui_MoreDialog

FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'more_window.ui'))


class SourceMoreWindow(BASE_CLASS, FORM_CLASS):
    def __init__(self):
        super().__init__()

        self.setupUi(self)

        # tab widget control flags
        self.location_tab_active = False
        self.relation_tab_active = False
        # end of tab widget control flags

        # setting default tab index flag according to current index
        self.setup_default_tab_index_flags()
        # end of setting default index flag

        self.more_main_tab.currentChanged.connect(self.activate_current_tab)  # when current tab changes

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

        # getting iface instance, to acces QGIS internals
        layer = iface.activeLayer()

        # looping through all selected features on QGIS kart
        for features in layer.selectedFeatures():
            for field in layer.fields():
                if field.name() == 'nvdbid':
                    nvdb_id = features[field.name()]
                    print(nvdb_id)

    # internal own class methods for inside uses
    def setup_default_tab_index_flags(self):
        if self.more_main_tab.currentIndex() == 0:  # 0 stedfesting tab
            self.location_tab_active = True
            self.relation_tab_active = False

        elif self.more_main_tab.currentIndex() == 1:  # 1 kobling tab
            self.relation_tab_active = True
            self.location_tab_active = False