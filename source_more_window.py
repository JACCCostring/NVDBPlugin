from qgis.PyQt import uic
from qgis.utils import iface
from qgis.core import QgsProject

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSignal
import os

#user defined modules
from .nvdbLesWrapper import AreaGeoDataParser

FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'more_window.ui'))

class SourceMoreWindow(BASE_CLASS, FORM_CLASS):
    new_relation_event = pyqtSignal(int, str) #signal for sending selected items
    unlink_btn_clicked = pyqtSignal() #signal for when unlink btn clicked
    
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        
        #tab widget control flags
        self.location_tab_active = False
        self.relation_tab_active = False
        #end of tab widget control flags
        
        #setting default tab index flag according to current index
        self.setup_default_tab_index_flags()
        
        #setting default values to table relation show
        self.setup_default_table_relation()
        
        #end of setting default index flag
        
        self.more_main_tab.currentChanged.connect(self.activate_current_tab) #when current tab changes
        self.table_relation_show.clicked.connect(self.item_clicked) #when any item is clicked in table
        self.unlink_from_parent_btn.clicked.connect(self.onUnlink_btn_clicked) #when unlink btn is clicked
        self.unlink_from_parent_btn.clicked.connect(self.display_msg) #comment here (can be call inside self.onUnlink_btn_clicked() method as well
        
        self.unlink_from_parent_btn.setEnabled(False)
        self.object_id_line.setReadOnly(True)

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

    def set_child_id(self, current_object, current_object_type):
        self.object_id_line.setText(f"{current_object_type} - {str(current_object)}")

    def feed_data(self, component_type: str = str(), data: dict = {}, active_parent: str = str()):
        if component_type == 'relation':
           #relation code here ...
            AreaGeoDataParser.set_env('test') #setting environment before use
            
            #getting possible parents
            possible_relation = AreaGeoDataParser.get_possible_parents(int(data['objekttype']))
            #print("Possible relations: " , possible_relation)

            #before population, check if object is linked to a parent
            #if it's then do not allow selection
            # if active_parent:
            #     self.table_relation_show.setEnabled(False)
            
            #populating relation component with possible parents
            self.populate_relation_component(possible_relation)

            #for parent_name, parent_id in active_parent.items():
               # self.current_linked_parent_lbl.setText(f"{parent_id} - {parent_name}")

        if component_type == 'location':
            #location code here ...
            pass

    def get_parent_status(self, parent_object):
        for parent_name, parent_id in parent_object.items():
            self.current_linked_parent_lbl.setText(f"{parent_id} - {parent_name}")
            #print(f"parent_id: {parent_id} - parent_name: {parent_name}")

    def populate_relation_component(self, data: dict = {}):
        row: int = 0

        self.table_relation_show.setRowCount(len(data))

        for item in data:
            name_item = QTableWidgetItem(item['name'])
            id_item = QTableWidgetItem(str(item['id']))

            self.table_relation_show.setItem(row, 0, id_item)
            self.table_relation_show.setItem(row, 1, name_item)

            row += 1

    def item_clicked(self, item):
        id = int(self.table_relation_show.item(item.row(), 0).text())
        name = self.table_relation_show.item(item.row(), 1).text()
        
        self.new_relation_event.emit(id, name)

    def onUnlink_btn_clicked(self):
        self.unlink_btn_clicked.emit()
        
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
            
    def setup_default_table_relation(self):
        label_headers = ['Objekttype', 'Navn']
        
        self.table_relation_show.setColumnCount(2)
        self.table_relation_show.setHorizontalHeaderLabels(label_headers)

    def display_msg(self):
        """layers_list = []

        for layer in QgsProject.instance().mapLayers().values():
            layers_list.append(layer)

        for lay in layers_list[2:]:
            if lay.name() != "OpenStreetMap":
                QgsProject.instance().removeMapLayer(lay.id())"""

        msg = QMessageBox()
        
        msg.setWindowTitle("Status")
        msg.setText("Operasjon sendt!")
        
        msg.exec()


    def set_status(self, status):
        if status in ("BEHANDLES", "VENTER"):
            self.status_fremdrfit_lbl.setStyleSheet(f"color: grey; font: 12pt 'MS Shell Dlg 2';")
        elif status in ("UTFØRT", "UTFØRT_OG_ETTERBEHANDLET"):
            self.status_fremdrfit_lbl.setStyleSheet(f"color: green; font: 12pt 'MS Shell Dlg 2';")
        elif status in ("AVVIST", "KANSELLERT"):
            self.status_fremdrfit_lbl.setStyleSheet(f"color: red; font: 12pt 'MS Shell Dlg 2';")

        self.status_fremdrfit_lbl.setText(status)
        self.avvist_lbl.clear()

    def set_msg_avvist(self, msg):
        self.avvist_lbl.setStyleSheet(f"color: red; font: 10pt 'MS Shell Dlg 2';")
        self.avvist_lbl.setText(msg)


    def set_login_status(self, status):
        if status == "logged":
            self.status_innlogging_lbl.setText("Logged")
            self.status_innlogging_lbl.setStyleSheet("color: green; font: 14pt 'MS Shell Dlg 2';")
        else:
            self.status_innlogging_lbl.setText('må logg på')
            self.status_innlogging_lbl.setStyleSheet("color: red; font: 14pt 'MS Shell Dlg 2';")

    def koble_fra_til_btn(self, dependant_mor, has_parent, status_login):
        self.avvist_lbl.clear()

        if not dependant_mor and has_parent and status_login:
            self.unlink_from_parent_btn.setEnabled(True)

        else:
            self.unlink_from_parent_btn.setEnabled(False)
            
            if dependant_mor:
                self.avvist_lbl.setText("Ojektet må ha mor!")
                self.avvist_lbl.setStyleSheet("color: grey; font: 14pt 'MS Shell Dlg 2';")
                
            elif not has_parent:
                self.avvist_lbl.setText("Ikke koblet til mor!")
                self.avvist_lbl.setStyleSheet("color: grey; font: 14pt 'MS Shell Dlg 2';")



