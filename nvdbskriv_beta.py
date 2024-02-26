# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'nvdbskriv_beta.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QCheckBox

from qgis.utils import iface
from qgis.core import *

from .nvdb_endringsset_status_window import Ui_windowProgress
from .nvdbLesWrapper import AreaGeoDataParser
from .tokenManager import TokenManager
from .delvisKorrigering import DelvisKorrigering

import requests, io, json
import xml.etree.ElementTree as ET 

class Ui_SkrivDialog(object):
    def __init__(self, data, listOfEgenskaper):
        self.data = data #all fetched nvdb objects in json format from Les vinduet 
        self.listOfEgenskaper = listOfEgenskaper #all fetched nvdb egenskaper from current nvdb searched objects
        self.successLogin = False
        self.idsOfSelectedItems = []
        self.progressWindowInstance = None
        self.progressWindowOpened = False
        self.info_after_sent_objects = []
        
#        self.apiLes = False
#        self.apiSkriv = False

    def setupUi(self, SkrivDialog):
        SkrivDialog.setObjectName("SkrivDialog")
        SkrivDialog.resize(828, 650) #width: 828, height: 848
        SkrivDialog.setMinimumSize(828, 650)
#        main windows background color
        SkrivDialog.setStyleSheet("background-color: rgb(76, 76, 76);")
        
        self.mainTab = QtWidgets.QTabWidget(SkrivDialog)
        self.mainTab.setGeometry(QtCore.QRect(10, 0, 791, 630)) #0, 0, 741, 500
        self.mainTab.setObjectName("mainTab")
        self.mainTab.setStyleSheet("color: rgb(238, 238, 238)")
        
        self.tabObjectList = QtWidgets.QWidget()
        self.tabObjectList.setObjectName("tabObjectList")

        self.tableSelectedObjects = QtWidgets.QTableWidget(self.tabObjectList)
        self.tableSelectedObjects.setGeometry(QtCore.QRect(0, 0, 811, 500)) #0, 0, 661, 500
        self.tableSelectedObjects.setObjectName("tableSelectedObjects")
        self.tableSelectedObjects.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 255, 0);\ncolor: rgb(0, 0, 255);")
        self.tableSelectedObjects.setColumnCount(0)
        self.tableSelectedObjects.setRowCount(0)
        
        self.updateSelectedObjectsBtn = QtWidgets.QPushButton(self.tabObjectList)
        self.updateSelectedObjectsBtn.setGeometry(QtCore.QRect(400, 530, 93, 28)) #670
        self.updateSelectedObjectsBtn.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 170, 255);\ncolor: rgb(52, 116, 14);")
        self.updateSelectedObjectsBtn.setObjectName("updateSelectedObjectsBtn")
        self.updateSelectedObjectsBtn.setText('oppdater list')
        
        self.deselectObjectBtn = QtWidgets.QPushButton(self.tabObjectList)
        self.deselectObjectBtn.setGeometry(QtCore.QRect(500, 530, 93, 28)) #670
        self.deselectObjectBtn.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 170, 255);\ncolor: rgb(52, 116, 14);")
        self.deselectObjectBtn.setObjectName("deselectObjectBtn")
        self.deselectObjectBtn.setText('fjern fra list')

        self.transferBtn = QtWidgets.QPushButton(self.tabObjectList)
        self.transferBtn.setGeometry(QtCore.QRect(0, 530, 93, 28)) #670
        self.transferBtn.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 170, 255);\ncolor: rgb(52, 116, 14);")
        self.transferBtn.setObjectName("transferBtn")
         
        self.check_endringsBtn = QtWidgets.QPushButton(self.tabObjectList)
        self.check_endringsBtn.setGeometry(QtCore.QRect(100, 530, 93, 28)) #670
        self.check_endringsBtn.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 170, 255);\ncolor: rgb(52, 116, 14);")
        self.check_endringsBtn.setObjectName("check_endringsBtn")
        
        self.mainTab.addTab(self.tabObjectList, "")
        
        self.tabLogin = QtWidgets.QWidget()
        self.tabLogin.setObjectName("tabLogin")
        
        self.label_3 = QtWidgets.QLabel(self.tabLogin)
        self.label_3.setGeometry(QtCore.QRect(370, 10, 55, 16))
        self.label_3.setObjectName("label_3")
        
        self.layoutWidget = QtWidgets.QWidget(self.tabLogin)
        self.layoutWidget.setGeometry(QtCore.QRect(11, 11, 178, 25))
        self.layoutWidget.setObjectName("layoutWidget")
        
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        
        self.usernameLine = QtWidgets.QLineEdit(self.layoutWidget)
        self.usernameLine.setStyleSheet("background-color: rgb(244, 239, 239);color: rgb(199, 88, 255);")
        self.usernameLine.setObjectName("usernameLine")
        
        self.horizontalLayout_2.addWidget(self.usernameLine)
        self.layoutWidget1 = QtWidgets.QWidget(self.tabLogin)
        self.layoutWidget1.setGeometry(QtCore.QRect(11, 92, 159, 25))
        self.layoutWidget1.setObjectName("layoutWidget1")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.label_2 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_2.setObjectName("label_2")
        
        self.horizontalLayout.addWidget(self.label_2)
        
        self.passwordLine = QtWidgets.QLineEdit(self.layoutWidget1)
        self.passwordLine.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordLine.setStyleSheet("background-color: rgb(244, 239, 239);color: rgb(199, 88, 255);")
        self.passwordLine.setObjectName("passwordLine")
        
        self.horizontalLayout.addWidget(self.passwordLine)
        
        self.statusLabel = QtWidgets.QLabel(self.tabLogin)
        self.statusLabel.setGeometry(QtCore.QRect(360, 50, 131, 32))
        self.statusLabel.setObjectName("statusLabel")
        
        self.widget = QtWidgets.QWidget(self.tabLogin)
        self.widget.setGeometry(QtCore.QRect(12, 170, 277, 30))
        self.widget.setObjectName("widget")
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        self.loginBtn = QtWidgets.QPushButton(self.widget)
        self.loginBtn.setObjectName("loginBtn")
        
        self.horizontalLayout_3.addWidget(self.loginBtn)
        
        self.updateBtn = QtWidgets.QPushButton(self.widget)
        self.updateBtn.setObjectName("updateBtn")
        
        self.horizontalLayout_3.addWidget(self.updateBtn)
        
        self.changeUserBtn = QtWidgets.QPushButton(self.widget)
        self.changeUserBtn.setObjectName("changeUserBtn")
        
        self.horizontalLayout_3.addWidget(self.changeUserBtn)
        
        self.mainTab.addTab(self.tabLogin, "")
        
        self.tabSettings = QtWidgets.QWidget()
        self.tabSettings.setObjectName("tabSettings")
        
        self.label_4 = QtWidgets.QLabel(self.tabSettings)
        self.label_4.setGeometry(QtCore.QRect(540, 20, 55, 16))
        
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.tabSettings)
        self.label_5.setGeometry(QtCore.QRect(10, 20, 55, 16))
        self.label_5.setObjectName("label_5")
        
        self.miljoCombo = QtWidgets.QComboBox(self.tabSettings)
        self.miljoCombo.setGeometry(QtCore.QRect(10, 50, 141, 22))
        self.miljoCombo.setObjectName("miljoCombo")
        
        self.nvdbLesLabel = QtWidgets.QLabel(self.tabSettings)
        self.nvdbLesLabel.setGeometry(QtCore.QRect(540, 50, 81, 16))
        
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        
        self.nvdbLesLabel.setFont(font)
        self.nvdbLesLabel.setStyleSheet("color: rgb(255, 0, 0);")
        self.nvdbLesLabel.setObjectName("nvdbLesLabel")
        
        self.nvdbSkrivLabel = QtWidgets.QLabel(self.tabSettings)
        self.nvdbSkrivLabel.setGeometry(QtCore.QRect(540, 80, 81, 16))
        
        self.loginMsg = QtWidgets.QLabel(self.tabLogin)
        self.loginMsg.setGeometry(QtCore.QRect(360, 90, 260, 25))
        self.loginMsg.setStyleSheet("color: rgb(255, 128, 0);")
        self.loginMsg.setText("")
        self.loginMsg.setObjectName("loginMsg")
        
        self.loginMsgfont = QtGui.QFont()
        self.loginMsgfont.setPointSize(14)
        self.loginMsgfont.setBold(False)
        self.loginMsgfont.setWeight(50)
        self.loginMsg.setFont(self.loginMsgfont)
        
        self.hideWindowBtn = QtWidgets.QPushButton(SkrivDialog)
        self.hideWindowBtn.setGeometry(QtCore.QRect(12, 597, 93, 28)) #795
        self.hideWindowBtn.setStyleSheet("background-color: rgb(244, 239, 239);\nborder-color: rgb(255, 170, 255);\ncolor: rgb(52, 116, 14);")
        self.hideWindowBtn.setObjectName("hideWindowBtn")
        self.hideWindowBtn.setText('skjul vinduet')
        
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        
        self.nvdbSkrivLabel.setFont(font)
        self.nvdbSkrivLabel.setStyleSheet("color: rgb(255, 0, 0);")
        self.nvdbSkrivLabel.setObjectName("nvdbSkrivLabel")
        
        self.checkStatusBtn = QtWidgets.QPushButton(self.tabSettings)
        self.checkStatusBtn.setGeometry(QtCore.QRect(540, 110, 93, 28))
        self.checkStatusBtn.setObjectName("checkStatusBtn")
        
        self.mainTab.addTab(self.tabSettings, "")

        self.retranslateUi(SkrivDialog)
        self.mainTab.setCurrentIndex(1)

        QtCore.QMetaObject.connectSlotsByName(SkrivDialog)
        
        self.defaultUILogin() #calling to set default UI login
        self.fixMiljo() #setting miljo data
        self.nvdbStatus() #calling nvdb status
        
#        setting columncount and headers here
        self.tableSelectedObjects.setColumnCount(3)
        tableSelectedObjectsHeaders = ['nvdbid', 'navn', 'vegref']
        
#        setting headers to table
        self.tableSelectedObjects.setHorizontalHeaderLabels(tableSelectedObjectsHeaders)
        
#        deativating edit triger to tableview and change of selection behavior
        self.tableSelectedObjects.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.tableSelectedObjects.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        #        connecting signals components
        self.loginBtn.clicked.connect(self.login)
        
        self.updateBtn.clicked.connect(self.updateLogin)
        
        self.checkStatusBtn.clicked.connect(self.nvdbStatus)
        
        self.changeUserBtn.clicked.connect(self.changeUser)
        
        self.hideWindowBtn.clicked.connect(lambda: SkrivDialog.hide())
        
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

    def retranslateUi(self, SkrivDialog):
        _translate = QtCore.QCoreApplication.translate
        SkrivDialog.setWindowTitle(_translate("SkrivDialog", "NVDB Skriv"))
        self.transferBtn.setText(_translate("SkrivDialog", "overfør valgt"))
        self.check_endringsBtn.setText(_translate("SkrivDialog", "sjekk endrings"))
#        self.cancelBtn.setText(_translate("SkrivDialog", "kanseller valgt"))
#        self.cancelAllBtn.setText(_translate("SkrivDialog", "kanseller alt"))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tabObjectList), _translate("SkrivDialog", "Objektlist"))
        self.label_3.setText(_translate("SkrivDialog", "Status"))
        self.label.setText(_translate("SkrivDialog", "Brukernavn"))
        self.label_2.setText(_translate("SkrivDialog", "Passord"))
        self.statusLabel.setText(_translate("SkrivDialog", "<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">må logg in</span></p></body></html>"))
        self.loginBtn.setText(_translate("SkrivDialog", "Log In"))
        self.updateBtn.setText(_translate("SkrivDialog", "Oppdater"))
        self.changeUserBtn.setText(_translate("SkrivDialog", "bytt bruker"))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tabLogin), _translate("SkrivDialog", "Login"))
        self.label_4.setText(_translate("SkrivDialog", "Status"))
        self.label_5.setText(_translate("SkrivDialog", "Miljø"))
        self.nvdbLesLabel.setText(_translate("SkrivDialog", "NVDB Les"))
        self.nvdbSkrivLabel.setText(_translate("SkrivDialog", "NVDB Skriv"))
        self.checkStatusBtn.setText(_translate("SkrivDialog", "check status"))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tabSettings), _translate("SkrivDialog", "instillinger"))






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
        url = self.miljo[self.miljoCombo.currentText()]
        username = self.usernameLine.text()
        password = self.passwordLine.text()
        
        tkManager = TokenManager(username, password, url)
        
        tokenObj = tkManager.getToken()
        
        # print(tokenObj)
        
        idToken = tokenObj['idToken']
        refreshToken = tokenObj['refreshToken']
        accessToken = tokenObj['accessToken']
                
        if idToken and refreshToken and accessToken != ' ':
            self.successLogin = True
            
            self.tokens = {
                'idToken': idToken, 
                'accessToken': accessToken, 
                'refreshToken': refreshToken
        }
        
        self.defaultUILogin() #calling to set new default UI according to access or not
        
        if self.successLogin == False:
            self.loginMsg.setText('Brukernavn eller passord er feil!')
            
        if self.successLogin:
            self.loginMsg.setText('')
        
    def defaultUILogin(self):
        if self.successLogin:
            self.statusLabel.setText('Logged')
            self.statusLabel.setStyleSheet("color: green; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(False)
            self.usernameLine.setEnabled(False)
            self.passwordLine.setEnabled(False)
        
        else:
            self.statusLabel.setText('må logg på')
            self.statusLabel.setStyleSheet("color: red; font: 14pt 'MS Shell Dlg 2';")
            self.loginBtn.setEnabled(True)
            self.usernameLine.setEnabled(True)
            self.passwordLine.setEnabled(True)
    
    
    def updateLogin(self):
        self.login()
        
    def nvdbStatus(self):
        apiStatusEndpoints = {
        'Produksjon': 'https://nvdbstatus-api.atlas.vegvesen.no/',
        'Utvikling': 'https://nvdbstatus-api.utv.atlas.vegvesen.no/',
        'Akseptansetest': 'https://nvdbstatus-api.test.atlas.vegvesen.no/'
        }
        
        endpoint = apiStatusEndpoints[self.miljoCombo.currentText()]
        url =  endpoint + 'api/v1/systems'
                
        response = requests.get(url)
        
        systems = json.loads(response.text)
        
        APILesName = ''
        APILesHealth = ''
        APISkrivName = ''
        APISkrivHealth = ''
        
        for system in systems['status']:
            if system['name'] == 'API Les':
                APILesName = system['name']
                APILesHealth = system['healthCondition']
            
            elif system['name'] == 'API Skriv':
                APISkrivName = system['name']
                APISkrivHealth = system['healthCondition']
        
# making sure api les/skriv flags are set to true or false
#        api les flag
        if APILesName == 'API Les' and APILesHealth == 'HEALTHY':
            self.apiLes = True
        
        elif APILesName == 'API Les' and APILesHealth != 'HEALTHY':
            self.apiLes = False
        
#        api skriv flag
        if APISkrivName == 'API Skriv' and APISkrivHealth == 'HEALTHY':
            self.apiSkriv = True
        
        elif APISkrivName == 'API Skriv' and APISkrivHealth != 'HEALTHY':
            self.apiSkriv = False
            
        self.nvdbStatusObj = {
            'APILesRunning': self.apiLes,
            'APISkrivRunning': self.apiSkriv
        }
        
#        print(self.apiLes, self.apiSkriv)
        
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
                
#         looping throug selectedObjects from Layer       
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

#        Posible Solution: loop throug selectedItems in tableview
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
        
    def getFieldsOfSelectedObject(self):
        layer = iface.activeLayer()

        selected_object_fields = {}
        nvdbid = None
        
        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')
                self.current_nvdbid = nvdbid
                
#        TODO: make this method iterable with n-elements nvdbid iterable
#        to make it usefull for more then 1 selected items from the table:

#        ex: num_nvdbids = self.getSelectedItemsInTable()
#        
#        for index_nvdbid in range(0, len(num_nvdbids)):
#            fields_selected_feature = self.getFieldsOfSelectedObject(num_nvdbids[index_nvdbid])
#            do something with fields_selected_feature dict
                            
        for feature in layer.selectedFeatures():
            for field in feature.fields():
                if 'nvdbid' in field.name():
                    if str(nvdbid) in str(feature[field.name()]):
                        for feat_field in feature.fields():
#                            print(feat_field.name(), ': ', feature[feat_field.name()])
                            
                            if 'Geometri' in feat_field.name():
                                self.geometry_found = feature.geometry().asWkt()
                                # print(self.geometry_found)
                                
                                if 'PointZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PointZ', 'Point Z')
                                    
                                if 'LineStringZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('LineStringZ', 'LineString Z')
                                
                                if 'PolygonZ' in self.geometry_found:
                                    self.geometry_found = self.geometry_found.replace('PolygonZ', 'Polygon Z')
                                
                            selected_object_fields[feat_field.name()] = feature[feat_field.name()]
                
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
    
    def getNVDBID_from_item(self):
        nvdbid = None
        
        for item in self.tableSelectedObjects.selectedItems():
            if item.isSelected():
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')
        
        return nvdbid
    
    def getIDsRelation(self, data):
#        data is a collection of objects from NVDB 
#        data is formed by nvdb python API in github
        id_collections = {}
        egenskapid = None
        
        for main_data in self.data:
            for _data in main_data:
                if _data == 'nvdbId':
                    if str(main_data[_data]) == self.getNVDBID_from_item():
                        for referense_data in main_data:
                            if referense_data == 'relasjoner':
                                for k, v in main_data[referense_data].items():
#                                    if k == 'foreldre' or 'barn': #vegobjekter relasjoner kun barn ikke foreldre
                                    if k == 'barn':
                                        
                                        for ss in v:
                                            for key, value in ss.items():
                                                if key == 'id':
                                                    egenskapid = value
                                                    
                                                if key == 'vegobjekter':
                                                    id_collections[egenskapid] = value
        return id_collections
    
    def getFieldFromSelectedObjects(self, data, field):
        # data argument is a dictionary allready populated with data, after objects is selected
        vegobjekt_field = None
        
        for key, value in data.items():
            if key == field:
                vegobjekt_field = value
        
        return vegobjekt_field
        
    def writeToNVDB(self):
        data = None
        data = self.getFieldsOfSelectedObject() #pay attention
        
        if self.successLogin == False: #if user is not logged in, then ask to log in again
            self.mainTab.setCurrentIndex(1)
        
        relations = self.getIDsRelation(self.data) #getting relasjoner av vegobjekter
        
        if data and self.successLogin: #if user is logged in and data no null then continue
            
            object_type = self.data[0]['objekttype'] #ex: Anttenna: 470, Veganlegg: 30
            
            vegobjekternavn = self.getFieldFromSelectedObjects(data, 'Navn')
            
            username = self.usernameLine.text()
            
            datakatalog_versjon = AreaGeoDataParser.getDatakatalogVersion(self.miljoCombo.currentText())
            
            skrivEndPoint = self.getMiljoSkrivEndpoint()
            
            sistmodifisert = AreaGeoDataParser.getSistModifisert(object_type, data['nvdbid'], 
                                                                                                        data['versjon'], 
                                                                                                        self.miljoCombo.currentText())
                        
            extra = {
                'nvdb_object_type': object_type, 
                'username': username, 
                'datakatalog_version': datakatalog_versjon,
                'endpoint': skrivEndPoint,
                'sistmodifisert': sistmodifisert,
                'current_nvdbid': self.current_nvdbid,
                'relation': relations, #dict
                'geometry_found': self.geometry_found,
                'objekt_navn': vegobjekternavn
            }
            
            token = self.tokens['idToken']
            
            # creating DelvisKorrigering object
            self.delvis = DelvisKorrigering(token, data, extra)
    
            # when new_endringsset_sent signal emited then call self.on_new_endringsset slot/method
            self.delvis.new_endringsset_sent.connect(self.on_new_endringsset)
            
            # when xml form finished,  and endringsett_form_done signal is triggered then post
            self.delvis.endringsett_form_done.connect(self.preparePost)
            
            # calling formXMLRequest method to form xml template
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
        if self.progressWindowInstance:
            self.progressWindowInstance.hide()
            self.progressWindowInstance = None
            
#        only make instance of windows if this is None
        if self.progressWindowInstance == None:
            self.progressWindowInstance = QtWidgets.QDialog()
            self.ui = Ui_windowProgress(self.info_after_sent_objects) #passing list of ids as parameter
            self.ui.setupUi(self.progressWindowInstance)
            self.progressWindowInstance.show()
            # self.progressWindowOpened = True
            
#        only shows windows again if this is allready opened
        # if self.progressWindowOpened and self.progressWindowInstance:
        #    self.progressWindowInstance.show()
    
    def on_new_endringsset(self, endringsset):
        # it meas new endringssett is ready and added to the list
        self.info_after_sent_objects.append(endringsset)
        
        # opening progress window after andringset is added to list
        self.openProgressWindow()
        
    def preparePost(self):
        # prepare_post will send post request after preparing it
        self.delvis.prepare_post()
        
    
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SkrivDialog = QtWidgets.QDialog()
    ui = Ui_SkrivDialog()
    ui.setupUi(SkrivDialog)
    SkrivDialog.show()
    sys.exit(app.exec_())