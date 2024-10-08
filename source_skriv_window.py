from PyQt5 import QtWidgets

########
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QCheckBox
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate, QDateTime, QTime
from PyQt5.QtCore import pyqtSignal

from .nvdb_endringsset_status_window import Ui_windowProgress  # dialog class

from .nvdbLesWrapper import AreaGeoDataParser
from .delvisKorrEgenskaperCase import DelvisKorrEgenskaperCase
from .tokenManager import TokenManager

from qgis.utils import iface
from qgis.core import *

import requests, io, json, time
import threading
import os

from qgis.PyQt import uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nvdbskriv_beta.ui'))


#########
class SourceSkrivDialog(QtWidgets.QDialog, FORM_CLASS):
    userLogged = pyqtSignal(str, dict)
    not_logged = pyqtSignal()
    
    endringsett_count_watcher = pyqtSignal(int)

    def __init__(self, data, listOfEgens):
        super().__init__()

        # init variables
        self.data = data  # all fetched nvdb objects in json format from Les vinduet
        self.listOfEgenskaper = listOfEgens  # all fetched nvdb egenskaper from current nvdb searched objects
        self.successLogin = False
        self.idsOfSelectedItems = []  # list of selected ids from QGIS kart layer
        self.progressWindowInstance = None  # windows instance
        self.progressWindowOpened = False  # to check if windows is allready opened
        self.progressWindowOpened = False  # to check if windows is already opened
        self.info_after_sent_objects = []  # all endringer sent to NVDB
        self.session_expired = False #for controlling time session expiration
        self.nvdbids_counter: int = int( 0 ) #for counting number of road objects sent
        self.list_of_nvdbids_var: list = []


        # setting up all UI
        self.setupUi(self)

        self.defaultUILogin()  # calling to set default UI login
        self.fixMiljo()  # setting miljo data
        self.nvdbStatus()  # calling nvdb status

        # self.check_endringsBtn.setEnabled( False )

        # set login tab at the start of the plug-in
        self.mainTab.setCurrentIndex(1)

        #        setting columncount and headers here
        # self.tableSelectedObjects.setColumnCount(3)
        self.tableSelectedObjects.setColumnCount(5)
        tableSelectedObjectsHeaders = ['nvdbid', 'navn', 'vegref', 'sent/ikke sent', 'grunn av']

        #        setting headers to table
        self.tableSelectedObjects.setHorizontalHeaderLabels(tableSelectedObjectsHeaders)

        #        deativating edit triger to tableview and change of selection behavior
        self.tableSelectedObjects.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tableSelectedObjects.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.response_endringsset.setText("")

        # saving time when application starts to compare later on

        # setting hour + 8, for expected time, so we can compare later
        # but date it's current day is need it as well, in case time of 8 hours
        # has passed but day as well, to make sure API Token is expired or no

        self.expected_time = QTime.currentTime()
        self.expected_date = QDate.currentDate()

        # expected day and minutes
        self.expected_day = self.expected_date.day() + 1
        # self.expected_day = self.expected_date.day()

        expected_minutes = self.expected_time.minute()
        # expected_minutes = self.expected_time.minute() + 1

        # expected hour
        self.expected_time.setHMS(self.expected_time.hour() + 8, expected_minutes, 0)
        # self.expected_time.setHMS(self.expected_time.hour(), expected_minutes, 0)

        # try to log in at the start of the windows, in case there
        # is allready a session started
        self.login()

        # end of

        #        connecting signals components
        self.loginBtn.clicked.connect(self.login)

        self.updateBtn.clicked.connect(self.updateLogin)

        self.checkStatusBtn.clicked.connect(self.nvdbStatus)

        self.changeUserBtn.clicked.connect(self.changeUser)

        self.hideWindowBtn.clicked.connect(lambda: self.hide())

        self.updateSelectedObjectsBtn.clicked.connect(lambda: self.selectedObjectsFromLayer())

        self.transferBtn.clicked.connect(self.writeToNVDB)

        self.check_endringsBtn.clicked.connect(self.openProgressWindow)

        #        self.tableSelectedObjects.itemClicked.connect(self.onItemSelected)

        self.deselectObjectBtn.clicked.connect(self.on_removeSelectedObject)

        #        iface.mapCanvas().selectionChanged.connect(lambda: self.selectedObjectsFromLayer())

        #        when miljø combobox index changed signals is emited
        self.miljoCombo.currentIndexChanged.connect(self.onMiljoChanged)

        #        username field and password when enter pressed signals
        self.usernameLine.returnPressed.connect(lambda: self.login())
        self.passwordLine.returnPressed.connect(lambda: self.login())
        
        #watching if counter get to max num of nvdbids selected from road objects to sent table widget
        self.endringsett_count_watcher.connect( self.onCountWatcherChanged )

    def fixMiljo(self):
        self.miljo = {
            'Produksjon': 'https://nvdbapiskriv.atlas.vegvesen.no/rest/v1/oidc/authenticate',
            'Utvikling': 'https://nvdbapiskriv.utv.atlas.vegvesen.no/rest/v1/oidc/authenticate',
            'Akseptansetest': 'https://nvdbapiskriv.test.atlas.vegvesen.no/rest/v1/oidc/authenticate',
            'Systemtest': 'https://nvdbapiskriv-stm.utv.atlas.vegvesen.no/rest/v1/oidc/authenticate'
        }

        self.miljoCombo.addItems({'Produksjon', 'Akseptansetest', 'Utvikling', 'Systemtest'})
        self.miljoCombo.setCurrentText('Akseptansetest')

    def login(self):
        # verifying if login time still valid
        # if login time is greater then 8 hours
        # then is not valid anymore, so we update login
        if self.login_time_expired():
            # getting new current time and re-configured self.expected_time
            # then setting new expected time to self.expected_time
            new_expected_time = QTime.currentTime()  # current time

            new_expected_minutes = new_expected_time.minute()  # setting current minute
            # new_expected_minutes = new_expected_time.minute() + 1

            new_expected_time.setHMS(new_expected_time.hour(), new_expected_minutes, 0)  # setting current time
            self.expected_time.setHMS(0, 0, 0)  # resetting expected time
            self.expected_time.setHMS(new_expected_time.hour() + 8, new_expected_minutes,
                                      0)  # setting current time to self.expected_time
            # self.expected_time.setHMS(new_expected_time.hour(), new_expected_minutes, 0)

            # but as well as time we need to think about the date
            # if login time is expired, that measn that we are here
            # next thing to do is to re-configure date again to current date + 1
            current_date = QDate.currentDate()
            current_day = current_date.day()

            new_expected_day = current_day + 1
            self.expected_day = 0  # reseting expected day
            self.expected_day = new_expected_day  # re-assigning new expected day

        url = self.miljo[self.miljoCombo.currentText()]

        try:
            if not os.environ['logged']:
                if not os.environ['logged']:

                    print('not existing !, setting logged ...')
                    os.environ['svv_user_name'] = self.usernameLine.text()
                    os.environ['svv_pass'] = self.passwordLine.text()

                    if os.environ['svv_user_name'] and os.environ['svv_pass']:
                        os.environ['logged'] = 'true'

        except KeyError:
            os.environ['svv_user_name'] = ''
            os.environ['svv_pass'] = ''
            os.environ['logged'] = ''

            return

        username = os.environ['svv_user_name']
        password = os.environ['svv_pass']

        # print(os.environ['svv_user_name'])
        # print(os.environ['svv_pass'])

        self.usernameLine.setText(username)
        self.passwordLine.setText(password)

        tkManager = TokenManager(username, password, url)

        tokenObj = tkManager.getToken()

        # print(tokenObj) debug

        idToken = tokenObj['idToken']
        refreshToken = tokenObj['refreshToken']
        accessToken = tokenObj['accessToken']

        if idToken and refreshToken and accessToken != ' ':
            self.successLogin = True

            # print('logged in')

            self.tokens = {
                'idToken': idToken,
                'accessToken': accessToken,
                'refreshToken': refreshToken
            }

            # emiting signal from here to nvdb_beta_dialog.py module
            self.userLogged.emit(self.usernameLine.text(), self.tokens)


        # if logging not succeded then, clear enviroment variables
        # pass, username and logged flag
        if not self.successLogin:
            os.environ['svv_user_name'] = ''
            os.environ['svv_pass'] = ''
            os.environ['logged'] = ''

        self.defaultUILogin()  # calling to set new default UI according to access or not

        if self.successLogin == False and self.usernameLine.text() != '' or self.passwordLine.text() != '':
            self.loginMsg.setText('Brukernavn eller passord er feil!')

        if self.successLogin:
            self.loginMsg.setText('')

    def defaultUILogin(self):
        self.response_endringsset.setText("")

        if self.successLogin:
            self.statusLabel.setText('Pålogget')
            self.statusLabel.setStyleSheet("color: green; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(False)
            self.usernameLine.setEnabled(False)
            # self.passwordLine.setEnabled(False)
            self.passwordLine.setReadOnly(True)
            #self.source_more_window.set_login_status(status="logged")
            self.login_status = True

        else:
            self.statusLabel.setText('må logge på')
            self.statusLabel.setStyleSheet("color: red; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(True)
            self.usernameLine.setEnabled(True)
            # self.passwordLine.setEnabled(True)
            self.passwordLine.setReadOnly(False)
            self.not_logged.emit()



    def updateLogin(self):
        self.login()

    def nvdbStatus(self):
        apiStatusEndpoints = {
            'Produksjon': 'https://nvdbstatus-api.atlas.vegvesen.no/',
            'Utvikling': 'https://nvdbstatus-api.utv.atlas.vegvesen.no/',
            'Akseptansetest': 'https://nvdbstatus-api.test.atlas.vegvesen.no/'
        }

        endpoint = apiStatusEndpoints[self.miljoCombo.currentText()]
        url = endpoint + 'api/v1/systemer'

        response = requests.get(url)

        if response.ok:
            systems = json.loads(response.text)

            APILesName = ''
            APILesHealth = ''
            APISkrivName = ''
            APISkrivHealth = ''

            for system in systems['systemer']:
                if system['navn'] == 'API Les':
                    APILesName = system['navn']
                    APILesHealth = system['helse']

                elif system['navn'] == 'API Skriv':
                    APISkrivName = system['navn']
                    APISkrivHealth = system['helse']

            # making sure api les/skriv flags are set to true or false
            #        api les flag
            if APILesName == 'API Les' and APILesHealth == 'FRISK':
                self.apiLes = True

            elif APILesName == 'API Les' and APILesHealth != 'FRISK':
                self.apiLes = False

            #        api skriv flag
            if APISkrivName == 'API Skriv' and APISkrivHealth == 'FRISK':
                self.apiSkriv = True

            elif APISkrivName == 'API Skriv' and APISkrivHealth != 'FRISK':
                self.apiSkriv = False

            self.nvdbStatusObj = {
                'APILesRunning': self.apiLes,
                'APISkrivRunning': self.apiSkriv
            }

            #        print(self.apiLes, self.apiSkriv)

            self.defaultUISettings()  # callinf default UI settings  after check status

    def defaultUISettings(self):
        #        API Les
        if self.nvdbStatusObj['APILesRunning']:
            self.nvdbLesLabel.setStyleSheet("color: green")

        if self.nvdbStatusObj['APILesRunning'] == False:
            self.nvdbLesLabel.setStyleSheet("color: red")

        #        API Skriv
        if self.nvdbStatusObj['APISkrivRunning']:
            self.nvdbSkrivLabel.setStyleSheet("color: green")

        if self.nvdbStatusObj['APISkrivRunning'] == False:
            self.nvdbSkrivLabel.setStyleSheet("color: red")

    def changeUser(self):
        self.usernameLine.clear()
        self.passwordLine.clear()

        os.environ['svv_user_name'] = ''
        os.environ['svv_pass'] = ''
        os.environ['logged'] = ''

        self.successLogin = False  # setting login to false again
        self.defaultUILogin()  # calling default ui again to set up default ui values
        
        self.not_logged.emit() #emitting signal again, for letting know in more_window

        self.usernameLine.setEnabled(True)
        self.passwordLine.setEnabled(True)

    def onMiljoChanged(self):
        self.successLogin = False

        self.defaultUILogin()

    def selectedObjectsFromLayer(self):
        layer = iface.activeLayer()
        selectedObjects = []
        fullInfoObjects = []

        for feature in layer.selectedFeatures():
            for field in feature.fields():
                key = field.name()
                value = feature[key]

                object = {key: value}

                selectedObjects.append(object)

        #         looping through selectedObjects from Layer
        for object in selectedObjects:

            if 'nvdbid' in object:
                for key in object:
                    fullInfoObjects.append({key: object[key]})

            if 'Navn' in object:
                for key in object:
                    fullInfoObjects.append({key: object[key]})

            if 'vegsystemreferanse' in object:
                for key in object:
                    fullInfoObjects.append({key: object[key]})
        
        #clrearing colors from old selected road objects or features
        self.reset_color_selected_rows()
        
        #        draw/set objects to UI
        self.setSelectedObjectsToUI(fullInfoObjects)
        
    def reset_color_selected_rows(self):
        for row in range(self.tableSelectedObjects.rowCount()):
            if self.list_of_nvdbids_var:
                if self.tableSelectedObjects.item(row, self.tableSelectedObjects.columnCount() - 1): #grunn av column
                    self.tableSelectedObjects.item(row, self.tableSelectedObjects.columnCount() - 1).setBackground(QtGui.QColor(255, 255, 255)) #last colum (grunn av)
                    self.tableSelectedObjects.setItem(row, self.tableSelectedObjects.columnCount() - 1, QTableWidgetItem(str('')))
                
                if self.tableSelectedObjects.item(row, self.tableSelectedObjects.columnCount() - 2): #status column
                    self.tableSelectedObjects.setItem(row, self.tableSelectedObjects.columnCount() - 2, QTableWidgetItem(str('')))
            
            
    def setSelectedObjectsToUI(self, objects):
        rows = 0  # rows for how many items will be laying

        #        counting rows, if nvdbid repeat then increment rows + 1
        #        nvdbid always present in the nvdb objects database
        for object in objects:
            if 'nvdbid' in object:
                rows += 1

            #        setting rows and calumns to the table
        self.tableSelectedObjects.setRowCount(rows)

        row = 0  # row for laying items

        for object in objects:
            if 'nvdbid' in object:
                self.tableSelectedObjects.setItem(row, 0, QTableWidgetItem(str(object['nvdbid'])))

            if 'Navn' in object:
                self.tableSelectedObjects.setItem(row, 1, QTableWidgetItem(object['Navn']))

            if 'vegsystemreferanse' in object:
                self.tableSelectedObjects.setItem(row, 2, QTableWidgetItem(object['vegsystemreferanse']))

                row += 1
    
    def set_status_sent_or_not(self, nvdbid: int, isSent: bool, reason: str) -> None:
        #first loop through all items
        for row in range(self.tableSelectedObjects.rowCount()):
            
            item = self.tableSelectedObjects.item(row, 0) #main item for data
            
            if item.text() == str(nvdbid):
                if not isSent:
                    start_msg_tag = reason.find('<message>')
                    end_msg_tag = reason.rfind('</message>')
                    
                    main_reason = reason[start_msg_tag + len(str('<message>')): end_msg_tag]
                    
                    self.tableSelectedObjects.setItem(row, 3, QTableWidgetItem('ikke sent'))
                    self.tableSelectedObjects.setItem(row, 4, QTableWidgetItem(main_reason)) #reason
                    
                    self.tableSelectedObjects.item(row, 4).setBackground(QtGui.QColor(255, 153, 153)) #backgound red color
            
                if isSent:
                    self.tableSelectedObjects.setItem(row, 3, QTableWidgetItem('sent'))
                    self.tableSelectedObjects.setItem(row, 4, QTableWidgetItem(reason)) #reason
                    
                    self.tableSelectedObjects.item(row, 4).setBackground(QtGui.QColor(204, 255, 153)) #backgound green color
    
    def on_removeSelectedObject(self):
        layer = iface.activeLayer()
        someSelected = False
        #        TODO: make sure only selected items are remove from layer and tableview
        
        '''
        Posible Solution: loop throug selectedItems in tableview
        if item selected then added to the self.idsOfSelectedItems
        only if item nvdbid doesn't exist in the list
        '''
        
        numSelectedItems = len(self.tableSelectedObjects.selectedItems())  # number of selected items

        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                if self.textFromTableItem(item, 'nvdbid') not in self.idsOfSelectedItems:
                    self.idsOfSelectedItems.append(self.textFromTableItem(item, 'nvdbid'))

        if numSelectedItems > 0:
            someSelected = True

        if someSelected:

            for field in layer.fields():  # loop throug all feature fields in active layer
                for feature in layer.selectedFeatures():  # loop throug all selected features in layer
                    for itemIdToDeselect in self.idsOfSelectedItems:  # loop throug all selected items from table
                        if 'nvdbid' in field.name():  # if field is nvdbid then
                            if str(itemIdToDeselect) in str(feature[field.name()]):  # if item id selected from table is = to layer feature id then
                                layer.deselect(feature.id())  # deselect feature
                                self.selectedObjectsFromLayer()  # re-read selected features from layer

            self.idsOfSelectedItems.clear()  # clearing list of items everytime remove method is called
            self.tableSelectedObjects.clearSelection()

    def textFromTableItem(self, item, columnName):
        #        pass
        row = item.row()
        column_index = 0  # 0 field by default

        #        try to substract only nvdbid field from table widge
        for _column in range(0, self.tableSelectedObjects.columnCount()):
            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()

            if columnName in columnText:
                column_index = _column

        nvdbid = self.tableSelectedObjects.item(row, column_index).text()
        self.idsOfSelectedItems.append(nvdbid)

    def getTextFieldFromColumnIndex(self, item, columnName):

        row = item.row()
        column_index = 0  # 0 field by default

        #        try to substract only nvdbid field from table widge
        for _column in range(0, self.tableSelectedObjects.columnCount()):
            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()

            if columnName in columnText:
                column_index = _column

        field_text = self.tableSelectedObjects.item(row, column_index).text()

        return field_text

    def onItemSelected(self, item):
        pass
        '''
        row = item.row()
        column_index = 0 #0 field by default
    
        #        try to substract only nvdbid field from table widge
        for _column in range(0, self.tableSelectedObjects.columnCount()):
            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()
    
            if 'nvdbid' in columnText:
                column_index = _column
    
        nvdbid = self.tableSelectedObjects.item(row, column_index).text()
        self.idsOfSelectedItems.append(nvdbid)
        '''
        
        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
                            # print(feat_field.name(), ': ', feature[feat_field.name()])
                            if 'Geometri' in feat_field.name():
                                self.geometry_found = feature.geometry().asWkt()

                                if 'PointZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PointZ', 'Point Z')

                                if 'LineStringZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('LineStringZ', 'LineString Z')

                                if 'PolygonZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PolygonZ', 'Polygon Z')

                            selected_object_fields[feat_field.name()] = feature[feat_field.name()]

        return selected_object_fields

    def list_of_nvdbids(self):
        nvdbid_list = []

        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')
                
                nvdbid_list.append(nvdbid)

        nvdbid_list = list(set(nvdbid_list))  # a Set() collection will remove duplicates
        
        # print('debug: list of IDs', nvdbid_list)
        
        return nvdbid_list

    def get_field_egenskaper_by_nvdbid(self, nvdbid):
        layer = iface.activeLayer()

        selected_object_fields = {}

        self.current_nvdbid = nvdbid

        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
                            # print(feat_field.name(), ': ', feature[feat_field.name()])

                            if 'Geometri' in feat_field.name():
                                self.geometry_found = feature.geometry().asWkt()

                                if 'PointZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PointZ', 'Point Z')

                                if 'LineStringZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('LineStringZ', 'LineString Z')

                                if 'PolygonZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PolygonZ', 'Polygon Z')
                            
                            # print(feat_field.name(), 'type', type(feature[feat_field.name()]))
                            
                            #if QDate or QDateTime type is found, then converted to Python str format
                            if isinstance(feature[feat_field.name()], (QDate, QDateTime)):
                                feature[feat_field.name()] = feature[feat_field.name()].toString('yyyy-MM-dd')
                            
                            selected_object_fields[feat_field.name()] = feature[feat_field.name()]

        return selected_object_fields

    def getSistModifisert(self, type, nvdbid, versjon):
        endpoint = self.getMiljoLesEndpoint() + '/' + 'vegobjekter' + '/' + str(type) + '/' + str(nvdbid) + '/' + str(
            versjon)

        header = {
            'Content-Type': 'application/xml',
            'X-Client': 'QGIS Skriv'
        }

        response = requests.get(endpoint, headers=header)

        json_data = json.loads(response.text)

        for data in json_data:
            if data == 'metadata':
                for key, value in json_data[data].items():
                    if key == 'sist_modifisert':
                        return value

    def get_road_object_relationship(self, nvdbid) -> dict:
        '''
        this method only  parsed road object's relationship
        allready laying  on the fetched data in self.data, not generic ones
        '''
        relation_collection: dict = {}
        opert: str = str()
        nvdbids_action: str = str()

        for refdata in self.data:
            for key, value in refdata.items():
                if key == 'nvdbId':
                    if str(refdata[key]) == nvdbid:
                        for key, value in refdata.items():
                            if key == 'relasjoner':
                                for rel_name, rel_value in value.items():
                                    if rel_name == 'barn':

                                        for relation in rel_value:

                                            try:
                                                nvdbids_action = relation['child_nvdbid']
                                                opert = relation['operation']
                                                print('tagging with ADD')

                                            except KeyError:
                                                print('tagging with UPDATE')
                                                opert = 'update'  # tagging for updating

                                            operation = opert

                                            relation_collection[relation['id']] = {
                                                'vegobjekter': relation['vegobjekter'], 'operation': operation,
                                                'nvdbid': nvdbids_action}

        print('relation to be sent: ', relation_collection)

        return relation_collection

    def getEspecificFieldContent(self, data, field):
        # data argument is a dictionary allready populated with data, after objects is selected
        vegobjekt_field = None

        for key, value in data.items():
            if key == field:
                vegobjekt_field = value

        return vegobjekt_field

    def writeToNVDB(self):
        '''
        verifying if login time still valid
        if login time is greater then 8 hours
        then is not valid anymore, so we update login
        '''
        if self.login_time_expired():
            self.login()  # update login

            # here we need to re-open status windows, for re-sending new tokens
            # and endringssett again
            self.progressWindowInstance = None
            self.openProgressWindow()

            return

        self.thread = threading.Thread(target=self.sennding_endrings_thread)
        self.thread.start()


    def sennding_endrings_thread(self):
        layer_modified_egenskaper = None
        token: str = str()

        try:
            token = self.tokens['idToken']

        except AttributeError:
            pass

        # get all nvdb id of selected features
        self.list_of_nvdbids_var = self.list_of_nvdbids()
        
        self.write_window_endrings_progressbar.setMaximum(len( self.list_of_nvdbids_var ))
        
        for nvdbid in self.list_of_nvdbids_var:
            # get egenskaper data from each of the nvdbids
            layer_modified_egenskaper = self.get_field_egenskaper_by_nvdbid(nvdbid)

            # continue with same precedure as before
            if self.successLogin == False:  # if user is not logged in, then ask to log in again
                self.mainTab.setCurrentIndex(1)

            if layer_modified_egenskaper and self.successLogin:  # if user is logged in and data no is populated then continue
                
                #sending status for user
                self.response_endringsset.setText(' sending ... ')
                
                road_object_type = self.data[0]['objekttype']  # ex: Anttenna: 470, Veganlegg: 30

                road_object_name = self.getEspecificFieldContent(layer_modified_egenskaper, 'Navn')

                username = self.usernameLine.text()

                datacatalog_version = AreaGeoDataParser.get_datacatalog_version(self.miljoCombo.currentText())

                env_write_endpoint = self.get_env_write_endpoint()
                
                sistmodifisert = AreaGeoDataParser.get_last_time_modified(road_object_type, layer_modified_egenskaper['nvdbid'], layer_modified_egenskaper['versjon'])
                
                #relations = self.get_road_object_relationship( self.current_nvdbid) #getting relasjoner av vegobjekter only childs not parent
                
                extra_data = {
                    'nvdb_object_type': road_object_type,
                    'username': username,
                    'datakatalog_version': datacatalog_version,
                    'endpoint': env_write_endpoint,
                    'sistmodifisert': sistmodifisert,
                    'current_nvdbid': nvdbid,
                    #'relation': relations,  # dict not need it. Only egenskaper sent
                    'geometry_found': self.geometry_found,
                    'objekt_navn': road_object_name
                }

                '''
                creating DelvisKorrEgenskaperCase instance, this class flow execution, first
                call object.formXMLRequest() method, then this method will emit a signal
                and that signal well react and call self.preparePost() method.

                and a the end of self.preparePost() method, then will make a call to object.prepare_post() method
                and then this method will make a call method object.startPosting().

                This last method will queued all sent endringssett to NVDB, and emit new_endringsset_sent signal
                then this signal react and call a on_new_endringsset slot/method, for adding or queuing all sent endringsset
                in a list
                
                Note: Signals and Slots must be connected in same order as coded here, because
                of how Qt works when queueing signals
                '''
                
                self.delvis = DelvisKorrEgenskaperCase(token, layer_modified_egenskaper, extra_data)

                self.delvis.new_endringsset_sent.connect(self.on_new_endringsset)

                self.delvis.endringsett_form_done.connect(self.preparePost)
                
                self.delvis.onEndringsett_fail.connect(self.set_status_sent_or_not) #when endringsett success/fail in Delvis object
                
                '''
                TODO:
                    for now we're using requests module for fetching HTTP data, and it do not
                    allow async but planing to use Asyncio and aioHttp module for async HTTP fetching.
                    
                    For now sleeping for half a second, ;)
                    
                '''
                time.sleep(0.5) #sleeping for half a second, to give time for the nex endringsett to be sent

                self.delvis.formXMLRequest(self.listOfEgenskaper)
            
                self.nvdbids_counter += 1 #counting
                
                self.endringsett_count_watcher.emit( self.nvdbids_counter )
            
            # self.delvis.formXMLRequest(self.listOfEgenskaper)
            
    def feed_new_list_egenskaper_and_data(self, new_data: dict = {}, new_list: dict = {}):            
        self.data = new_data
        self.listOfEgenskaper = new_list
        
    def get_env_write_endpoint(self):
        currentMiljo = self.miljoCombo.currentText()
        
        url = None

        if 'Produksjon' in currentMiljo:
            url = 'https://nvdbapiskriv.atlas.vegvesen.no/rest/v3/endringssett'

        if 'Akseptansetest' in currentMiljo:
            url = 'https://nvdbapiskriv.test.atlas.vegvesen.no/rest/v3/endringssett'

        if 'Utvikling' in currentMiljo:
            url = 'https://nvdbapiskriv.utv.atlas.vegvesen.no/rest/v3/endringssett'

        return url

    def getMiljoLesEndpoint(self):
        currentMiljo = self.miljoCombo.currentText()
        lesUrl = None

        if 'Produksjon' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.atlas.vegvesen.no'

        if 'Akseptansetest' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.test.atlas.vegvesen.no'

        if 'Utvikling' in currentMiljo:
            lesUrl = 'https://nvdbapiles-v3.utv.atlas.vegvesen.no'

        return lesUrl

    def getEspecificFieldValue(self, field_name):
        layer = iface.activeLayer()

        especific_field = {}
        nvdbid = None

        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')

        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
                            if field_name in feat_field.name():
                                especific_field[feat_field.name()] = feature[feat_field.name()]

        return especific_field

    def openProgressWindow(self):
        '''
        verifying if login time still valid
        if login time is greater then 8 hours
        then is not valid anymore, so we update login
        '''
        if self.login_time_expired():
            # print('login expired!')

            self.login()  # update login
            
            '''
            making session expired to True, so when try opening status windows
            can know if session has been expired or not, and no matter what
            it can re-assign new token
            '''
            self.session_expired = True
            '''
            here we need to re-open status windows, for re-sending new tokens
            and endringssett again
            self.progressWindowInstance = None
            '''
            
            return

        if self.progressWindowInstance:
            self.progressWindowInstance.hide()
            self.progressWindowInstance = None

        #        only make instance of windows if this is None
        if self.progressWindowInstance == None:
            
            # print('size of ids collected:', len( self.info_after_sent_objects ) )
            
            self.progressWindowInstance = Ui_windowProgress(self.info_after_sent_objects)

            '''
            re-assigning new generated token if session has been expired
            at this point if session has been expired, then will loop through hole
            list looking for any token and replacing it with new generated
            '''
            if self.session_expired:
                for item in self.info_after_sent_objects:
                    for endring in item:
                        endring['token'] = self.tokens['idToken']

            self.progressWindowInstance.show()
            
            '''
            making session expired to False after showing the windows
            after this it means that session is first time loging or re-loging
            '''
            self.session_expired = False

    def on_new_endringsset(self, endringsset):
        # print('new endringsett sent===================')
        self.info_after_sent_objects.append(endringsset)
        
        if self.progressWindowInstance:
            self.progressWindowInstance.populate_table( self.info_after_sent_objects )

    def preparePost(self):
        # Lambda functions pass correct feedback and color to function
        
        #not need it for now
        # self.delvis.response_error.connect(lambda error: self.update_status(error, "red"))
        # self.delvis.response_success.connect(lambda successful: self.update_status(successful, "green"))

        # prepare_post will send post request after preparing it
        self.delvis.prepare_post()

    def update_status(self, text, color):
        self.response_endringsset.setText(text)
        self.response_endringsset.setStyleSheet(f"color: {color}; font: 12pt 'MS Shell Dlg 2';")
        
        # self.openProgressWindow()
        # self.check_endringsBtn.setEnabled( True )
    
    def onCountWatcherChanged(self, count):
        if count == len( self.list_of_nvdbids_var ):
            # self.check_endringsBtn.setEnabled( True )
            
            self.update_status('Ferdig', 'green')
            
            self.nvdbids_counter = 0 #restaring counter
        
        self.write_window_endrings_progressbar.setValue(count)
            
    def login_time_expired(self):
        '''
        verify if current time and start time hours
        is over 8 hours difference, 8 hours is the set hours
        given to a token to be expired

        method it will return true if current_time time
        it's 8 hours greater or equal to expected_time

        expected time is taken at the begining of the application
        and it's assigned 8 hours later, then the time was a that point
        '''

        '''
        substract current time
        minutes of current time must be substracted
        since setHMS method modify hole time
        so it's need it to have consistency
       '''
        current_time = QTime.currentTime()
        current_minutes = current_time.minute()
        current_time.setHMS(current_time.hour(), current_minutes, 0)

        '''
        but as well we need current day for comparing if day => then expected
        in case this function reutn true due to current and expected time might
        to be true, then the expected day calculated when the software started, 
        can be compared against the current day
        '''
        current_date = QDate.currentDate()
        current_day = current_date.day()

        # debug
        # print('current day ', current_day, ' - expected day ', self.expected_day)
        # print('current time ', current_time, ' - expected time ', self.expected_time)


        '''
        #comparing current and expected day, if this case happens
        #to be true, then means another day has passed and API Token
        #has expired even if current and expected hour case happens to be true
        '''

        '''
        for Ex: current hour = 08:00 and expected hour = 15:00
        but program was started yestarday 08:00, in this case
        the hours case happens to be false, and not true, but API Token
        is already expired
        '''

        '''
        a solution to this would be to check if has passed one or more days 
        since the software was started
        '''
        if current_day >= self.expected_day:
            return True
        '''
        comparing time if current time is >= then expected time
        then return true
        '''
        if current_time >= self.expected_time:
            return True

        return False