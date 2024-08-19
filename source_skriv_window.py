from PyQt5 import QtWidgets

# from .nvdbskriv_beta import Ui_SkrivDialog
########
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QCheckBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate, QTime

from .nvdb_endringsset_status_window import Ui_windowProgress #dialog class

from .nvdbLesWrapper import AreaGeoDataParser
from .delvisKorrigering import DelvisKorrigering
from .tokenManager import TokenManager
from qgis.utils import iface
from qgis.core import *

import requests, io, json
import threading

from .helper import Logger #for logging, watch out
import os
import json

from qgis.PyQt import uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nvdbskriv_beta.ui'))
    
#########
class SourceSkrivDialog(QtWidgets.QDialog, FORM_CLASS):
    userLogged = pyqtSignal(str)
    
    def __init__(self, data, listOfEgenskaper):
        super().__init__()
        
        #init variables
        self.data = data #all fetched nvdb objects in json format from Les vinduet 
        self.listOfEgenskaper = listOfEgenskaper #all fetched nvdb egenskaper from current nvdb searched objects
        self.successLogin = False
        self.idsOfSelectedItems = [] #list of selected ids from QGIS kart layer
        self.progressWindowInstance = None #windows instance
        self.progressWindowOpened = False #to check if windows is allready opened
        self.progressWindowOpened = False #to check if windows is already opened
        self.info_after_sent_objects = [] #all endringer sent to NVDB
        self.session_expired = False

        #setting up all UI
        self.setupUi(self)
        
        self.defaultUILogin() #calling to set default UI login
        self.fixMiljo() #setting miljo data
        self.nvdbStatus() #calling nvdb status

        #self.my_logger = Logger()

        # log to console/file
        #self.my_logger.write_log("console")
        #self.my_logger.disable_logging()

        self.logger1 = Logger()

        #set login tab at the start of the plug-in
        self.mainTab.setCurrentIndex(1)

#        setting columncount and headers here
        self.tableSelectedObjects.setColumnCount(3)
        tableSelectedObjectsHeaders = ['nvdbid', 'navn', 'vegref']
        
#        setting headers to table
        self.tableSelectedObjects.setHorizontalHeaderLabels(tableSelectedObjectsHeaders)
        
#        deativating edit triger to tableview and change of selection behavior
        self.tableSelectedObjects.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tableSelectedObjects.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.response_endringsset.setText("")

        #saving time when application starts to compare later on
        
        #setting hour + 8, for expected time, so we can compare later
        #but date it's current day is need it as well, in case time of 8 hours
        #has passed but day as well, to make sure API Token is expired or no
        
        self.expected_time = QTime.currentTime()
        self.expected_date = QDate.currentDate()
        
        #expected day and minutes
        self.expected_day = self.expected_date.day() + 1
        # self.expected_day = self.expected_date.day()
        
        expected_minutes = self.expected_time.minute()
        # expected_minutes = self.expected_time.minute() + 1
        
        #expected hour
        self.expected_time.setHMS(self.expected_time.hour() + 8, expected_minutes, 0)
        # self.expected_time.setHMS(self.expected_time.hour(), expected_minutes, 0)
        
        #try to log in at the start of the windows, in case there
        #is allready a session started
        self.login()
        
        #end of
        
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
        #verifying if login time still valid
        #if login time is greater then 8 hours
        #then is not valid anymore, so we update login        
        if self.login_time_expired():
            #getting new current time and re-configured self.expected_time
            #then setting new expected time to self.expected_time
            new_expected_time = QTime.currentTime() #current time
            
            new_expected_minutes = new_expected_time.minute()#setting current minute
            # new_expected_minutes = new_expected_time.minute() + 1
            
            new_expected_time.setHMS(new_expected_time.hour(), new_expected_minutes , 0) #setting current time
            self.expected_time.setHMS(0, 0, 0) #resetting expected time
            self.expected_time.setHMS(new_expected_time.hour() + 8, new_expected_minutes, 0) #setting current time to self.expected_time
            # self.expected_time.setHMS(new_expected_time.hour(), new_expected_minutes, 0)
            
            #but as well as time we need to think about the date
            #if login time is expired, that measn that we are here
            #next thing to do is to re-configure date again to current date + 1
            current_date = QDate.currentDate()
            current_day = current_date.day()
            
            new_expected_day = current_day + 1
            self.expected_day = 0 #reseting expected day
            self.expected_day = new_expected_day #re-assigning new expected day

        url = self.miljo[self.miljoCombo.currentText()]
        
        try:
            if not os.environ['logged']:
                if not os.environ['logged']:

                    #self.my_logger.logger.info('not existing !, setting logged ...')
                    os.environ['svv_user_name'] = self.usernameLine.text()
                    os.environ['svv_pass'] = self.passwordLine.text()
                    
                    if os.environ['svv_user_name'] and os.environ['svv_pass']:
                        os.environ['logged'] = 'true'
                    
        except KeyError:
            os.environ['svv_user_name'] =''
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

        #DEBUG
        print(tokenObj)
       # self.my_logger.logger.debug(f"tokenObj: {tokenObj}")

        idToken = tokenObj['idToken']
        refreshToken = tokenObj['refreshToken']
        accessToken = tokenObj['accessToken']
                
        if idToken and refreshToken and accessToken != ' ':
            self.successLogin = True
            self.logger1.log("logged in", "console")
            #print('logged in')
            #self.my_logger.logger.info("logged in")

            self.tokens = {
                'idToken': idToken, 
                'accessToken': accessToken, 
                'refreshToken': refreshToken
        }
            
            #emiting signal from here to nvdb_beta_dialog.py module
            self.userLogged.emit(self.usernameLine.text())
            
        #if logging not succeded then, clear enviroment variables
        #pass, username and logged flag
        if not self.successLogin:
            os.environ['svv_user_name'] =''
            os.environ['svv_pass'] = ''
            os.environ['logged'] = ''
        
        self.defaultUILogin() #calling to set new default UI according to access or not
        
        if self.successLogin == False and self.usernameLine.text() != '' or self.passwordLine.text() != '':
            self.loginMsg.setText('Brukernavn eller passord er feil!')
            
        if self.successLogin:
            self.loginMsg.setText('')
        
    def defaultUILogin(self):

        self.response_endringsset.setText("")

        if self.successLogin:
            self.statusLabel.setText('Logged')
            self.statusLabel.setStyleSheet("color: green; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(False)
            self.usernameLine.setEnabled(False)
            #self.passwordLine.setEnabled(False)
            self.passwordLine.setReadOnly(True)
        else:
            self.statusLabel.setText('må logg på')
            self.statusLabel.setStyleSheet("color: red; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(True)
            self.usernameLine.setEnabled(True)
            #self.passwordLine.setEnabled(True)
            self.passwordLine.setReadOnly(False)


    def updateLogin(self):
        self.login()
        
    def nvdbStatus(self):
        apiStatusEndpoints = {
        'Produksjon': 'https://nvdbstatus-api.atlas.vegvesen.no/',
        'Utvikling': 'https://nvdbstatus-api.utv.atlas.vegvesen.no/',
        'Akseptansetest': 'https://nvdbstatus-api.test.atlas.vegvesen.no/'
        }
        
        endpoint = apiStatusEndpoints[self.miljoCombo.currentText()]
        url =  endpoint + 'api/v1/systemer'
                
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
            
            print(self.apiLes, self.apiSkriv)
            #self.my_logger.logger.info(f"{self.apiLes}, {self.apiSkriv}")

            self.defaultUISettings() #callinf default UI settings  after check status
    
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
        
        os.environ['svv_user_name'] =''
        os.environ['svv_pass'] = ''
        os.environ['logged'] = ''
        
        self.successLogin = False #setting login to false again
        self.defaultUILogin() #calling default ui again to set up default ui values
        
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
                
                object = {key : value }

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
        
#        draw/set objects to UI
        self.setSelectedObjectsToUI(fullInfoObjects)

        print(f"Full info objects: {fullInfoObjects}")

    def setSelectedObjectsToUI(self, objects):
        rows = 0 #rows for how many items will be laying

#        counting rows, if nvdbid repeat then increment rows + 1
#        nvdbid always present in the nvdb objects database
        for object in objects:
            if 'nvdbid' in object:
                rows += 1 
        
#        setting rows and calumns to the table
        self.tableSelectedObjects.setRowCount(rows)

        row = 0 #row for laying items
                
        for object in objects:
            if 'nvdbid' in object:
                self.tableSelectedObjects.setItem(row, 0, QTableWidgetItem(str(object['nvdbid'])))
                
            if 'Navn' in object:
                self.tableSelectedObjects.setItem(row, 1, QTableWidgetItem(object['Navn']))
            
            if 'vegsystemreferanse' in object:
                self.tableSelectedObjects.setItem(row, 2, QTableWidgetItem(object['vegsystemreferanse']))
                
                row += 1
                        
    def on_removeSelectedObject(self):        
        layer = iface.activeLayer()
        someSelected = False
#        TODO: make sure only selected items are remove from layer and tableview

#        Possible Solution: loop through selectedItems in tableview
#        if item selected then added to the self.idsOfSelectedItems
#        only if item nvdbid doesn't exist in the list

        numSelectedItems = len(self.tableSelectedObjects.selectedItems()) #number of selected items
        
        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                if self.textFromTableItem(item, 'nvdbid') not in self.idsOfSelectedItems:
                    self.idsOfSelectedItems.append(self.textFromTableItem(item, 'nvdbid'))
                
        if numSelectedItems > 0:
            someSelected = True
            
        if someSelected:
            
            for field in layer.fields(): #loop throug all feature fields in active layer
                for feature in layer.selectedFeatures(): #loop throug all selected features in layer
                    for itemIdToDeselect in self.idsOfSelectedItems: #loop throug all selected items from table
                        if 'nvdbid' in field.name(): #if field is nvdbid then
                            if str(itemIdToDeselect) in str(feature[field.name()]): #if item id selected from table is = to layer feature id then
                                layer.deselect(feature.id()) #deselect feature
                                self.selectedObjectsFromLayer() #re-read selected features from layer
            
            self.idsOfSelectedItems.clear() #clearing list of items everytime remove method is called
            self.tableSelectedObjects.clearSelection()
    
    def textFromTableItem(self, item, columnName):
#        pass
        row = item.row()
        column_index = 0 #0 field by default
        
        #        try to substract only nvdbid field from table widge
        for _column in range(0, self.tableSelectedObjects.columnCount()):
            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()
            
            if columnName in columnText:
                column_index = _column
        
        nvdbid = self.tableSelectedObjects.item(row, column_index).text()
        self.idsOfSelectedItems.append(nvdbid)
        
    def getTextFieldFromColumnIndex(self, item, columnName):
        
        row = item.row()
        column_index = 0 #0 field by default
        
        #        try to substract only nvdbid field from table widge
        for _column in range(0, self.tableSelectedObjects.columnCount()):
            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()
            
            if columnName in columnText:
                column_index = _column
        
        field_text = self.tableSelectedObjects.item(row, column_index).text()
        
        return field_text
        
    def onItemSelected(self, item):
        pass
#        row = item.row()
#        column_index = 0 #0 field by default
#        
#        #        try to substract only nvdbid field from table widge
#        for _column in range(0, self.tableSelectedObjects.columnCount()):
#            columnText = self.tableSelectedObjects.horizontalHeaderItem(_column).text()
#            
#            if 'nvdbid' in columnText:
#                column_index = _column
#        
#        nvdbid = self.tableSelectedObjects.item(row, column_index).text()
#        self.idsOfSelectedItems.append(nvdbid)
        
    def getFieldEgenskaper(self):
        layer = iface.activeLayer()

        selected_object_fields = {}
        nvdbid = None
        
        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')
                self.current_nvdbid = nvdbid
                
        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
                            print(feat_field.name(), ': ', feature[feat_field.name()])
                            #self.my_logger.logger.info(f"{feat_field.name()} : {feature[feat_field.name()]}")
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
        
        nvdbid_list = list(set(nvdbid_list)) #remove duplicates
        return nvdbid_list
        
    def getFieldEgenskaperByNVDBid(self, nvdbid):
        layer = iface.activeLayer()

        selected_object_fields = {}
        
        self.current_nvdbid = nvdbid
        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
                            print(feat_field.name(), ': ', feature[feat_field.name()])
                            #self.my_logger.logger.info(f"{feat_field.name()} : {feature[feat_field.name()]}")

                            if 'Geometri' in feat_field.name():
                                self.geometry_found = feature.geometry().asWkt()
                                
                                if 'PointZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PointZ', 'Point Z')
                                    
                                if 'LineStringZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('LineStringZ', 'LineString Z')
                                
                                if 'PolygonZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PolygonZ', 'Polygon Z')

                            selected_object_fields[feat_field.name()] = feature[feat_field.name()]

        #print("selected_object_fields: ", selected_object_fields)
        #lst = json.loads(selected_object_fields["Assosierte Belysningspunkt"])
        #temp_list = lst["innhold"]
        #new_list = [item for item in temp_list if item['verdi'] == 537698071]

        #lst["innhold"] = new_list
        #selected_object_fields["Assosierte Belysningspunkt"] = json.dumps(lst)

        #print("selected_object_fields: (after_change)", selected_object_fields)

        return selected_object_fields
        
    def getSistModifisert(self, type, nvdbid, versjon):
        endpoint = self.getMiljoLesEndpoint() + '/' + 'vegobjekter' + '/' + str(type) + '/' + str(nvdbid) + '/' + str(versjon)
                
        header = {
            'Content-Type': 'application/xml',
            'X-Client': 'QGIS Skriv'
        }
        
        response = requests.get(endpoint, headers = header)
        
        json_data = json.loads(response.text)
        
        for data in json_data:
            if data == 'metadata':
                for key, value in json_data[data].items():
                    if key == 'sist_modifisert':
                        return value
    
    def getVegObjektRelasjoner(self, nvdbid)->dict:
        #this method only  parsed road object's relationship
        #allready laying  on the fetched data in self.data, not generic ones
        
        relation_collection: dict = {}
        # relation_id = None
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
                                                
                                            except KeyError:
                                                opert = 'update' #tagging for updating later insted of removing
                                                
                                            operation = opert
                                            
                                            relation_collection[relation['id']] = {'vegobjekter': relation['vegobjekter'], 'operation': operation, 'nvdbid': nvdbids_action}
        
        print('relation to be sent: ', relation_collection)

        return relation_collection
        
    def getEspecificFieldContent(self, data, field):
        # data argument is a dictionary already populated with data, after objects is selected
        vegobjekt_field = None
        
        for key, value in data.items():
            if key == field:
                vegobjekt_field = value
        
        return vegobjekt_field
        
    def writeToNVDB(self):
        #verifying if login time still valid
        #if login time is greater than 8 hours
        #then is not valid anymore, so we update login
        if self.login_time_expired():
            self.login() # update login
            
            #here we need to re-open status windows, for re-sending new tokens
            #and endringssett again
            self.progressWindowInstance = None
            self.openProgressWindow()
            
            return
            
        self.thread = threading.Thread(target=self.sennding_endrings_thread)
        self.thread.start()

    
    def sennding_endrings_thread(self):
        egenskaperfields = None
        token: str = str()
        
        try:
            token = self.tokens['idToken']
            
        except AttributeError:
            pass
            
        #get all nvdb id of selected features
        for nvdbid in self.list_of_nvdbids():
            print(f"nvdb: {nvdbid}")
        #get egenskaper data from each of the nvdbids
            egenskaperfields = self.getFieldEgenskaperByNVDBid(nvdbid)
            
        #continue with same precedure as before
            if self.successLogin == False: #if user is not logged in, then ask to log in again
                self.mainTab.setCurrentIndex(1)
            
            if egenskaperfields and self.successLogin: #if user is logged in and data no is populated, then continue
                
                object_type = self.data[0]['objekttype'] #ex: Anttenna: 470, Veganlegg: 30
                
                vegobjektnavn = self.getEspecificFieldContent(egenskaperfields, 'Navn')
                
                username = self.usernameLine.text()
                
                datakatalog_versjon = AreaGeoDataParser.getDatakatalogVersion(self.miljoCombo.currentText())
                
                miljoSkrivEndepunkter = self.getMiljoSkrivEndpoint()
                
                sistmodifisert = AreaGeoDataParser.getSistModifisert(object_type, egenskaperfields['nvdbid'], egenskaperfields['versjon'])
                
                relations = self.getVegObjektRelasjoner( self.current_nvdbid) #getting relasjoner av vegobjekter only childs not parents
                extra = {
                    'nvdb_object_type': object_type, 
                    'username': username, 
                    'datakatalog_version': datakatalog_versjon,
                    'endpoint': miljoSkrivEndepunkter,
                    'sistmodifisert': sistmodifisert,
                    'current_nvdbid': self.current_nvdbid,
                    'relation': relations, #dict
                    'geometry_found': self.geometry_found,
                    'objekt_navn': vegobjektnavn
                }
            
                # creating DelvisKorrigering object
                self.delvis = DelvisKorrigering(token, egenskaperfields, extra)

                # when new_endringsset_sent signal emited then call self.on_new_endringsset slot/method
                self.delvis.new_endringsset_sent.connect(self.on_new_endringsset)

                # when xml form finished,  and endringsett_form_done signal is triggered then prepare post
                self.delvis.endringsett_form_done.connect(self.preparePost)

                # when some events UB happens on DelvisKorrigering class side
                #self.delvis.response_error.connect(lambda: print('something went wrong! '))

                print("self.listOfEgenskaper", self.listOfEgenskaper)

                # calling formXMLRequest method to form delviskorrigering xml template
                self.delvis.formXMLRequest(self.listOfEgenskaper)

    def getMiljoSkrivEndpoint(self):
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
        #verifying if login time still valid
        #if login time is greater then 8 hours
        #then is not valid anymore, so we update login
        if self.login_time_expired():
            print('login expired!')
            #self.my_logger.logger.info("Login expired! ")

            self.login() # update login
            
            #making session expired to True, so when try opening status windows
            #can know if session has been expired or not, and no matter what
            #it can re-assign new token
            self.session_expired = True
            
            #here we need to re-open status windows, for re-sending new tokens
            #and endringssett again
            # self.progressWindowInstance = None
            
            # self.openProgressWindow() #be carefull it can be a loop and block main thread
            return
            
        if self.progressWindowInstance:
            self.progressWindowInstance.hide()
            self.progressWindowInstance = None
            
#        only make instance of windows if this is None
        if self.progressWindowInstance == None:
            # self.progressWindowInstance = QtWidgets.QDialog()
            self.progressWindowInstance = Ui_windowProgress(self.info_after_sent_objects)

            #self.my_logger.logger.info(self.info_after_sent_objects)

            #re-assigning new generated token if session has been expired
            #at this point if session has been expired, then will loop through hole
            #list looking for any token and replacing it with new generated
            if self.session_expired:
                for item in self.info_after_sent_objects:
                    for endring in item:
                        endring['token'] = self.tokens['idToken']
            
            # self.ui.setupUi(self.progressWindowInstance)
            self.progressWindowInstance.show()
            
            #making session expired to False after showing the windows
            #after this it means that session is first time loging or re-loging
            self.session_expired = False
            
            # self.progressWindowOpened = True
            
#        only shows windows again if this is already opened
        # if self.progressWindowOpened and self.progressWindowInstance:
        #    self.progressWindowInstance.show()
    
    def on_new_endringsset(self, endringsset):
        self.info_after_sent_objects.append(endringsset)
        # opening progress window after andringset is added to list
        # self.openProgressWindow()
        
    def preparePost(self):
        # when some events UB happens on DelvisKorrigering class side

        #self.delvis.response_error.connect(lambda error: print('Error! ', error))

        # Lambda functions pass correct feedback and color to function
        self.delvis.response_error.connect(lambda error: self.update_status(error, "red"))
        self.delvis.response_success.connect(lambda successful: self.update_status(successful, "green"))

        # prepare_post will send post request after preparing it
        self.delvis.prepare_post()

    def update_status(self, text, color):
        self.response_endringsset.setText(text)
        self.response_endringsset.setStyleSheet(f"color: {color}; font: 12pt 'MS Shell Dlg 2';")

    def login_time_expired(self):
        #verify if current time and start time hours
        #is over 8 hours difference, 8 hours is the set hours
        #given to a token to be expired
        
        #method it will return true if current_time time
        #it's 8 hours greater or equal to expected_time
        
        #expected time is taken at the begining of the application
        #and it's assigned 8 hours later, then the time was a that point
        
        #substract current time
        #minutes of current time must be substracted
        #since setHMS method modify hole time
       #so it's need it to have consistency
        current_time = QTime.currentTime()
        current_minutes = current_time.minute()
        current_time.setHMS(current_time.hour(), current_minutes, 0)
        
        #but as well we need current day for comparing if day => then expected
        #in case this function reutn true due to current and expected time might
        #to be true, then the expected day calculated when the software started, 
        #can be compared against the current day
        current_date = QDate.currentDate()
        current_day = current_date.day()
        
        #debug
        print('current day ', current_day, ' - expected day ', self.expected_day)
        print('current time ', current_time, ' - expected time ', self.expected_time)

       # self.my_logger.logger.debug(f"current day {current_day} - expected day {self.expected_day}")
       # self.my_logger.disable_logging()
        #self.my_logger.logger.debug(f"current time {current_time} - expected time {self.expected_time}")


        #comparing current and expected day, if this case happens
        #to be true, then means another day has passed and API Token
        #has expired even if current and expected hour case happens to be true
        
        #for Ex: current hour = 08:00 and expected hour = 15:00
        #but program was started yestarday 08:00, in this case
       #the hours case happens to be false, and not true, but API Token
      #is already expired
     
        #a solution to this would be to check if has passed one or more days 
       #since the software was started
        if current_day >= self.expected_day:
           return True
           
        #comparing time if current time is >= then expected time
        #then return true
        if current_time >= self.expected_time:
            return True
        
        return False