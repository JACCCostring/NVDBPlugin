import sys
import os
import inspect

nvdblibrary = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
nvdblibrary = nvdblibrary.replace('\\', '/')
nvdblibrary = nvdblibrary + '/nvdbapi'

## Hvis vi ikke klarer å importere nvdbapiv3 så prøver vi å føye
## mappen nvdblibrary til søkestien. 
try: 
    import nvdbapiv3
except ModuleNotFoundError:
    print( "Fant ikke nvdbapiv3 i sys.path, legger til mappen", nvdblibrary)
    sys.path.append( nvdblibrary ) 
    
    try: 
        import nvdbapiv3
    except ModuleNotFoundError as e:
        print( "\nImport av nvdbapiv3 feiler for", nvdblibrary  )
        raise ModuleNotFoundError( "==> Variabel nvdblibrary skal peke til mappen https://github.com/LtGlahn/nvdbapi-V3  <==" )
            
    else: 
        print( "SUKSESS - kan importere nvdbapiv3 etter at vi la til", nvdblibrary, "i sys.path" )
else:
    print( "HURRA - vi kan importere nvdbapiv3 " ) 


from nvdbapiv3 import nvdbFagdata, nvdbVegnett
from .nvdbapiV3qgis3 import  nvdb2kart, nvdbsok2qgis, url2kart, nvdb2kartListe

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.utils import iface
from qgis.core import *

from PyQt5.QtWidgets import QCompleter, QVBoxLayout, QLabel, QTableWidgetItem, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import  QSortFilterProxyModel, pyqtSignal, QAbstractTableModel

from .nvdbskriv_beta import Ui_SkrivDialog

from .nvdbLesWrapper import AreaGeoDataParser
#========================================
#includes need it for development
import os
import json
import requests
import threading

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NvdbBetaProductionDialog
                                 A QGIS plugin
 nvdb plugin to filtrate and show objects belonging to the norwegian roads
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-05-12
        git sha              : $Format:%H$
        copyright            : (C) 2023 by SVV
        email                : alexander.casado@vegvesen.no
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt5 import QtCore

import os

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nvdb_beta_dialog_base.ui'))


class NvdbBetaProductionDialog(QtWidgets.QDialog, FORM_CLASS):
    ready_for_setting_searched_objekt = pyqtSignal(list)
    setting_each_uiItem_inTable = pyqtSignal(int, dict, tuple, dict)
    amount_of_vegobjekter_collected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """Constructor."""
        super(NvdbBetaProductionDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.skrivWindowInstance = None #making skriv window null
        self.skrivWindowOpened = False #making windows opened false
        
#        development starts here
#        setting up all data need it for starting up
        
#        making filter edit box unabled when program start
        self.filterByLineEdit.setEnabled(False)
        self.openSkrivWindowBtn.setEnabled(False) #setting not enabled before search is done!
        self.changeObjectsSize.setEnabled(False)
        
#        dictionary with andpoints necessary for environment
        self.environment = {
            'Produksjon': 'https://nvdbapiles-v3.atlas.vegvesen.no',
            'Utvikling': 'https://nvdbapiles-v3.utv.atlas.vegvesen.no',
            'Akseptansetest': 'https://nvdbapiles-v3.test.atlas.vegvesen.no',
            'Systemtest': 'https://nvdbapiles-v3-stm.utv.atlas.vegvesen.no'
        }

#        creating a QStandardItemModel for being able to connect itemChange() signal
#        rows, columns and headres will be assign later on self.setObjectsToUI() method
        self.tableViewResultModel = QStandardItemModel()
        
#        proxy model, to filter table view data on any column
        self.proxyModel = QSortFilterProxyModel()
        
        self.proxyModel.setSourceModel(self.tableViewResultModel)
        self.proxyModel.setFilterKeyColumn(-1) #-1 means all columns
        self.proxyModel.setFilterCaseSensitivity(0) #0 means insensitive
        
#        set combo box data to choose environmen if production/test/development
        self.comboEnvironment.addItems({'Produksjon', 'Utvikling', 'Akseptansetest', 'Systemtest'})
        
#        selecting a default environment
        self.comboEnvironment.setCurrentText('Akseptansetest')
#        setting an environment for default
        AreaGeoDataParser.setEnvironmentEndPoint(self.environment[self.comboEnvironment.currentText()])
        
#        setting up  combobox default values
        self.operatorCombo.addItems({'ikke verdi', '>', '<', '>=', '<=', '=', '!='})
        self.operatorCombo.setCurrentIndex(-1)
        
#        deativating  combobox when starting
#        self.egenskapBox.setEnabled(False)
        self.operatorCombo.setEnabled(False)
        self.verdiField.setEnabled(False)
        
#        deactivating some UI components
        self.searchObjectBtn.setEnabled(False)
        self.visKartCheck.setEnabled(False)
        
#        autocompletion for nvdb field
        listObjectNames = self.fixNVDBObjects()
        self.setCompleterNVDBObjects(listObjectNames)
        
#        autocompletion for fylke field
        listOfCounties = self.fixFylkeObjects()
        self.setCompleterFylkeObjects(listOfCounties)
        
#        autocompletion for kommune field
        listOfCommunities = self.fixCommunityObjects()
        self.setCompleterCommunityObjects(listOfCommunities)
                
#        connecting signals and slots

#        very important to fecth kommuner when field fylke change
        self.fylkeField.editingFinished.connect(self.checkComunitiesInCounty)
        
#        when seacrh button pressed
        self.searchObjectBtn.clicked.connect(self.searchObj)
        
#        when vis i kart checkbox active then
        self.visKartCheck.clicked.connect(self.onVisIKart)
        
#        noen egenskap i UI skal være not enable til user skriver input
        self.nvdbIdField.editingFinished.connect(self.onIdCatalogEdited)
        
#        when an item in table widget is clicked then
#        self.tableResult.itemClicked.connect(self.onItemClicked)
        
        self.tableResult.clicked.connect(self.onItemClicked)
        
#        when egenskap box change current item then 
        self.egenskapBox.currentIndexChanged.connect(self.onEgenskapChanged)
        
#        when operator box change then
        self.operatorCombo.currentIndexChanged.connect(self.onOperatorChanged)
        
#        when filtering the search in real time
        self.filterByLineEdit.textChanged.connect(self.proxyModel.setFilterRegExp)
                
#        when current index in miljø combobox changed then
        self.comboEnvironment.currentIndexChanged.connect(lambda: AreaGeoDataParser.setEnvironmentEndPoint(self.environment[self.comboEnvironment.currentText()]))
        
#        when open button clicked then
        self.openSkrivWindowBtn.clicked.connect(self.openSkrivWindow)
        
#        when selecting any feature from the active layer, then
        iface.mapCanvas().selectionChanged.connect(self.onAnyFeatureSelected)

#        when changing objects size in layer then
        self.changeObjectsSize.valueChanged.connect(self.on_objectSizeOnLayerChange)

        
#        rest of methods===============================
    def fixNVDBObjects(self):
#        all nvdb object types no all objects, to simulate datakatalog id
        nvdbObjects = []
        
        try:
            nvdbObjects = AreaGeoDataParser.fetchAllNvdbObjects()
            
            listObjectNames = []
            self.listOfnvdbObjects = {}
            
            for key, value in nvdbObjects.items():
                listObjectNames.append(key)
                self.listOfnvdbObjects[key] = value
        
        except Exception:
            print('datakatalog ikke lastett opp!')
            
        return listObjectNames
        
    def fixFylkeObjects(self):
        counties = []
        
        try:
            counties = AreaGeoDataParser.counties()
            
            listOfCountiesNames = []
            self.listOfCounties = {}
            self.reversListOfCounties = {}
            
            for key, value in counties.items():
                listOfCountiesNames.append(key)
                self.listOfCounties[key] = value
                self.reversListOfCounties[value] = key
        
        except Exception:
            print('flyke ikke lastett opp!')
            
        return listOfCountiesNames
        
    def fixCommunityObjects(self):
        communities = []
        
        try:
            communities = AreaGeoDataParser.communities()
            
            listOfCommunities = []
            self.listOfCommunitiesObjects = {}
            self.reversListOfCommunities = {}
            
            for key, value in communities.items():
                listOfCommunities.append(key)
                self.listOfCommunitiesObjects[key] = value
                self.reversListOfCommunities[value] = key
        
        except Exception:
            print('kommuner ikke lastett opp!')
            
        return listOfCommunities
        
    def checkComunitiesInCounty(self):
        data = []
        
        if self.fylkeField.text() == '':
#            print('empty')
            data = self.fixCommunityObjects()
            self.setCompleterCommunityObjects(data)
        
        elif self.fylkeField.text() != '': 
            text = self.fylkeField.text()
            for key, value in AreaGeoDataParser.communitiesInCounties.items():
                try:
                    
                    if value == self.listOfCounties[text]:
                        data.append(key)
                    
                except Exception:
                    pass
                
        self.setCompleterCommunityObjects(data)
                
    def setCompleterNVDBObjects(self, data):
        autoCompleter = QCompleter(data)
        autoCompleter.setCaseSensitivity(False)
        
        self.nvdbIdField.setCompleter(autoCompleter)
        
    def setCompleterFylkeObjects(self, data):
        autoCompleter = QCompleter(data)
        autoCompleter.setCaseSensitivity(False)
        
        self.fylkeField.setCompleter(autoCompleter)
        
    def setCompleterCommunityObjects(self, data):
        autoCompleter = QCompleter(data)
        autoCompleter.setCaseSensitivity(False)
        
        self.kommuneField.setCompleter(autoCompleter)
        
    def searchObj(self):
#        here search is prepared depending on which filters user has stablished
        
        #clearing tableview results everytime user search new road object
        if self.tableViewResultModel.rowCount() > 0:
            self.tableViewResultModel.clear()

#        removing layres just in case there are some actives, before a new search
        self.removeActiveLayers()
        
#        when searchObj execute then vis kart options is enabled and checked is falsed
        self.visKartCheck.setEnabled(True)
        self.visKartCheck.setChecked(False)
        
#        clearing layer map in QGIS in case exist 
        self.removeActiveLayers()
            
        if self.nvdbIdField.text() != '':
            nvdbId = self.listOfnvdbObjects[self.nvdbIdField.text()]
            self.v = nvdbFagdata(int(nvdbId))
            
#            --check nvdb envairoment
            if self.comboEnvironment.currentText() == 'Produksjon':
                self.v.miljo('prod')
            
            if self.comboEnvironment.currentText() == 'Utvikling':
                self.v.miljo('utv')
            
            if self.comboEnvironment.currentText() == 'Akseptansetest':
                self.v.miljo('test')
        
        if self.fylkeField.text() in self.listOfCounties:
            fylke = self.listOfCounties[self.fylkeField.text()]
            self.v.filter( { 'fylke': int(fylke) } )
        
        if self.kommuneField.text() in self.listOfCommunitiesObjects:
            kommune = self.listOfCommunitiesObjects[self.kommuneField.text()]
            self.v.filter( { 'kommune': int(kommune) } )
            
        if self.vegreferanseField.text() != '':
            self.v.filter( { 'vegsystemreferanse': self.vegreferanseField.text() } )
        
#        only if egenskapbox, operatorBox and verdi fields are populated then
        if self.egenskapBox.currentText() != '' and self.operatorCombo.currentText() != '' and self.verdiField.text() != '':

#            some aux variables
            egensk = self.listOfEgenskaper[self.egenskapBox.currentText()]
            egenskAndVerdi = ''
            
#            some aux variables
            key = self.verdiField.text()
            verdi = self.verdiField.text()
            operator = self.operatorCombo.currentText()

#            some type checks
            
            if self.verdierDictionary:
                verdi = self.verdierDictionary[key]
            
            if not self.verdierDictionary and AreaGeoDataParser.egenskapDataType() == 'Tall': #if datatype is integer
                verdi = int(verdi)
                
            if not self.verdierDictionary and AreaGeoDataParser.egenskapDataType() != 'Tall': #otherwise treat it like string
                verdi = "'" + verdi + "'"
            
            egenskAndVerdi = f"egenskap({egensk}){operator}{verdi}"
            
            self.v.filter( {'egenskap': egenskAndVerdi })
        
        #threading
        target = self.handle_threaded_search_objeckt
        
        self.thread_search_objekt = threading.Thread(target = target)
        
        #warn of search has started
        self.search_status_label.setText('Samling vegobjekter ...')
        
        #warning of search status has collected road objects
        self.amount_of_vegobjekter_collected.connect(lambda vegobjekter_amount: self.search_status_label.setText(f'samlet {vegobjekter_amount} objekter'))
        
        #making sure QProgressbar is set to zero before setting new values
        #on a new object search
        if self.search_object_progress_bar.value() > 0:
            self.search_object_progress_bar.setValue(0)
        
        #connecting signal when objects ready for UI
        self.ready_for_setting_searched_objekt.connect(self.prepareObjectsForUI)
        
        self.thread_search_objekt.start()
        # self.thread_search_objekt.join()
        
#        if skriv windows open then hide it, make it none and set self.skrivWindowOpened false
        
        if self.skrivWindowOpened:
            self.skrivWindowInstance.hide()
            self.skrivWindowInstance = None
            self.skrivWindowOpened = False
            
#            this btn needs to be dissable if skriv windows was opened before the search
            self.openSkrivWindowBtn.setEnabled(False)  
    
    def handle_threaded_search_objeckt(self):
#        retrieve data with applied filters
        max_obj_search = 1000
        steps = 1
        sliced_data = []
        self.data = None
        self.times_to_run: int = 0 
        
        self.data = self.v.to_records()
        
        #warn status label amount of road objects collected
        data_size = len(self.data)
        self.amount_of_vegobjekter_collected.emit(data_size)
        
        #slicing data to show in table not in source data to sliced_data = 5000, 
        #only if it's over that number
        if data_size > max_obj_search:
            
            sliced_data = self.data[0: max_obj_search: steps]
            
            self.current_num_road_objects = len(sliced_data)
        
        #if not then, just copy data source to sliced_data anyway
        #without modifying/slicing data size
        elif data_size < max_obj_search:
            sliced_data = self.data
            
            self.current_num_road_objects = len(sliced_data)
    
        objects_for_ui = self.makeMyDataObjects(sliced_data)
        #undefined behavior when emiting signal, then prepareObjectsForUI method
        #is calling itself multiple times, so self.times_to_run is to controll this behavior
        self.times_to_run += 1 
        
        self.ready_for_setting_searched_objekt.emit(objects_for_ui)

    def makeMyDataObjects(self, data):
        listObjects = []
        
        for element in data:
            for e in enumerate(element):
                key = e[1]
                obj = { key: element[key] }
                        
                listObjects.append(obj)
          
        return listObjects
        
    def onVisIKart(self, checked):
        if checked:
        #     #threading
        #     target = self.showing_object_in_map
            
        #     self.thread_showing_objekt_iKart = threading.Thread(target = target)
            
        #     self.thread_showing_objekt_iKart.start()
            
            self.v.refresh()
            nvdbsok2qgis(self.v)

#        setting size slider widget for objects size enabled, after features are in layer
            self.changeObjectsSize.setEnabled(True)
        
        else:
            self.removeActiveLayers()
#            when vis i kart option not checked in the current search, then just disable openSkrivWindow button
            self.openSkrivWindowBtn.setEnabled(False)
    
    def showing_object_in_map(self):
        self.v.refresh()
        nvdbsok2qgis(self.v)
        
        # self.thread_showing_objekt_iKart.join()
    
    def onIdCatalogEdited(self):
        self.searchObjectBtn.setEnabled(True)
        
        #        setting list of agenskaper objects
        self.listOfEgenskaper = {}
        
#        clean egenskaper combobox anyway
        self.egenskapBox.clear()
        
        if self.listOfEgenskaper:
            self.listOfEgenskaper.clear() #cleaning before use in case of re-use
        
        is_nvdbfield_valid = self.verifyNvdbField(self.nvdbIdField.text())
        print('is nvdb field valid', is_nvdbfield_valid)
        
        if is_nvdbfield_valid:
            egenskaper = AreaGeoDataParser.egenskaper(self.listOfnvdbObjects[self.nvdbIdField.text()])
        
            for key, value in egenskaper.items():
                self.egenskapBox.addItem(key)
                self.listOfEgenskaper[key] = value
            
            self.egenskapBox.addItem('ikke verdi') #adding aditional value to combo
            
    #     setting size slider widget for objects size not enabled, after features are in layer
            self.changeObjectsSize.setEnabled(False)
            
    #        removing layres just in case there are some actives
    #        self.removeActiveLayers()
    
    def verifyNvdbField(self, vegobjekt_type):
        for key, value in self.listOfnvdbObjects.items():
            if key == vegobjekt_type:
                return True
        
        return False
        
    def prepareObjectsForUI(self, objects):
        if self.times_to_run == 1:
            columns = self.parseHeaders(objects)
            index = self.indexHaders(columns)
        
            self.tableViewResultModel.setColumnCount(len(columns))
            self.tableViewResultModel.setHorizontalHeaderLabels(columns)
            
            #if better if range start from 0 in case only 1 road object is fetched
            self.search_object_progress_bar.setRange(0, self.current_num_road_objects)
            
            # thread_task_funct = self.threaded_loop_for_preparing_UI
            # thread_args = [objects, index]
            
            # self.thread_loop = threading.Thread(target = thread_task_funct, args = thread_args)
            
            # self.setting_each_uiItem_inTable.connect(self.set_objects_to_tableView)
            
            # self.thread_loop.start()
            # self.thread_loop.join()
            
            items = []
            row = 0
            
            try:
            #try starts here ...
            #parsing columns for adding to UI
                columns = self.parseHeaders(objects)
                index = self.indexHaders(columns)
        
                self.tableViewResultModel.setColumnCount(len(columns))
                self.tableViewResultModel.setHorizontalHeaderLabels(columns)
            
                for object in objects:
                    for obj in enumerate(object):
                        for idx in index:
                            if obj[1] == idx['header']:
                                # print('headers')
                                
                                if obj[1] == 'fylke': #if header is fylke, then use name instead of fylke number
                                    numFylke = object[obj[1]]
                                    nameFylke = self.reversListOfCounties[numFylke]
                                    object[obj[1]] = nameFylke
                                    
                                if obj[1] == 'kommune':  #if header is kommune, then use name instead of kommune number
                                    numKommune = object[obj[1]]
                                    nameKommune = self.reversListOfCommunities[numKommune]
                                    object[obj[1]] = nameKommune
                                    
                                self.tableViewResultModel.setRowCount(row + 1)

                                newItem = QStandardItem(str(object[obj[1]]))
                                
                                self.tableViewResultModel.setItem(row, int(idx['index']), newItem)
                                
                                self.tableResult.setModel(self.proxyModel)
                            
                                if obj[1] == 'geometri':
                                    row = row + 1
                                
                                # set real time filter enabled when search is done searching and setting up objects UI.
                                self.filterByLineEdit.setEnabled(True)
                                self.search_object_progress_bar.setValue(row)
            
            except Exception: #try ends here ...
                print('exception!')
                
         # making it zero again
        self.times_to_run = 0
            
    def threaded_loop_for_preparing_UI(self, objects, index):
        pass
        # items = []
        # row = 0
        
        # try:
        #try starts here ...
        #parsing columns for adding to UI
            # columns = self.parseHeaders(objects)
            # index = self.indexHaders(columns)
    
            # self.tableViewResultModel.setColumnCount(len(columns))
            # self.tableViewResultModel.setHorizontalHeaderLabels(columns)
    
        #     for object in objects:
        #         for obj in enumerate(object):
        #             for idx in index:
        #                 if obj[1] == idx['header']:
                                
        #                     if obj[1] == 'fylke': #if header is fylke, then use name instead of fylke number
        #                         numFylke = object[obj[1]]
        #                         nameFylke = self.reversListOfCounties[numFylke]
        #                         object[obj[1]] = nameFylke
                                    
        #                     if obj[1] == 'kommune':  #if header is kommune, then use name instead of kommune number
        #                         numKommune = object[obj[1]]
        #                         nameKommune = self.reversListOfCommunities[numKommune]
        #                         object[obj[1]] = nameKommune
                                    
        #                     # self.setting_each_uiItem_inTable.emit(row, object, obj, idx)
        #                     self.tableViewResultModel.setRowCount(row + 1)

        #                     newItem = QStandardItem(str(object[obj[1]]))
                                                
        #                     self.tableViewResultModel.setItem(row, int(idx['index']), newItem)
                                                
        #                     self.tableResult.setModel(self.proxyModel)
        
        #                     if obj[1] == 'geometri':
        #                         row = row + 1
                                
        #                     self.filterByLineEdit.setEnabled(True)
                        
        # except Exception: #try block ends here ...
        #     print('exception!')
    
    def set_objects_to_tableView(self, row, object, obj, idx):
        pass
        # self.tableViewResultModel.setRowCount(row + 1)

        # newItem = QStandardItem(str(object[obj[1]]))
                            
        # self.tableViewResultModel.setItem(row, int(idx['index']), newItem)
                            
        # self.tableResult.setModel(self.proxyModel)
        
        #setting progressbar value for each table item
        # self.search_object_progress_bar.setValue(row)
        
        # self.filterByLineEdit.setEnabled(True)
        
    def parseHeaders(self, objects):
        headers = []
        validHeaders =[]
        
        for obj in objects:
            if obj in headers:
                break
                
            headers.append(obj)
                
        for data in headers:
            for key in enumerate(data):
                validHeaders.append(key[1])
            
        return validHeaders
        
    def indexHaders(self, headers):
        list = []
        counter = 0
        
        for header in headers:
            index = {
            'index': counter,
            'header': header
            }
            
            counter = counter + 1
            
            list.append(index)
            
        return list
    
    def onItemClicked(self, index):
        data = self.substractItemData(index)
        
        self.copyNvdbId.setText(data['nvdbId'])
        self.copyVegRef.setText(data['vref'])
        
#        when click any item then select object in layer
        nvdbid = data['nvdbId']

        layer = iface.activeLayer()
        
        if self.visKartCheck.isChecked():
            for feature in layer.getFeatures():
                for field in layer.fields():
                    if 'nvdbid' in field.name():
                        if str(nvdbid) in str(feature[field.name()]):
                            layer.select(feature.id())
                
    def substractItemData(self, index):
        #for now the proxy model is the one in charge for filtrering
        #so the index from proxy model are different then the child model
        #a conversion it's need it from proxy index to child index in the view
        
        source = self.proxyModel.mapToSource(index) #so we convert from proxy index to the table model index
        row = source.row()
        
        nvdbId = None
        vref = None
        
        try:
            #starts here ...
            for column in range(0, self.tableViewResultModel.columnCount()):
                itemColumHeader = self.tableViewResultModel.horizontalHeaderItem(column)
                
                if itemColumHeader.text() == 'nvdbId':
                    resultNvdbId = self.tableViewResultModel.item(row, column)
                    nvdbId = resultNvdbId.text()
                    
                elif itemColumHeader.text() == 'vref':
                    resultVref = self.tableViewResultModel.item(row, column)
                    vref = resultVref.text()
                
        except Exception:
            pass
            
        return {'nvdbId': nvdbId, 'vref': vref}
        
    def onEgenskapChanged(self):
        index = self.egenskapBox.currentIndex()
        
        if self.egenskapBox.itemText(index) != 'ikke verdi':
#            fetch sub egenskaper for better autocompletoin in verdi field
            self.subEgenskaper()
            self.operatorCombo.setEnabled(True)
            
        else:
            idx = self.operatorCombo.findText('ikke verdi')
            self.operatorCombo.setCurrentIndex(idx) #on each iteration onOperatorChange method is also called
            self.operatorCombo.setEnabled(False)
#        self.verdiField.setEnabled(True)
        
    def onOperatorChanged(self):
        if self.operatorCombo.currentText() == 'ikke verdi':
            self.verdiField.clear()
            self.verdiField.setEnabled(False)
            self.operatorCombo.setEnabled(False)
            
        else:
            self.verdiField.setEnabled(True)
#            when operator is selected then we want auto-completion to verdie field
#            self.subEgenskaper()
            
    def removeActiveLayers(self):
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        
        for name in names:
            if name != 'OpenStreetMap':
                self.removeL(name)
            
    def subEgenskaper(self):
        nvdbid = 0
        
        try:
            nvdbId = self.listOfnvdbObjects[self.nvdbIdField.text()]
            
        except Exception:
            pass
            
        especificEgenskap = self.egenskapBox.currentText()
        
        verdier = AreaGeoDataParser.especificEgenskaper(nvdbId, especificEgenskap)
        
        self.verdierDictionary = {}
        verdierList = []
        
#        cleaning verdierDictionary in case of already data in it
        if self.verdierDictionary:
            self.verdierDictionary.clear()
        
#        loop through list of verdier and set the auto-completion to verdi field in UI
        for key, value in verdier.items():
            verdierList.append(str(key)) #key should be string type
            
            self.verdierDictionary[str(key)] = value #key should be string types
            
        self.setCompleterVerdierObjects(verdierList)
#        print(self.verdierDictionary)
        
    def setCompleterVerdierObjects(self, data):
        autoCompleter = QCompleter(data)
        autoCompleter.setCaseSensitivity(False)
        
        self.verdiField.setCompleter(autoCompleter)
                
    def removeL(self, name):
        qinst = QgsProject.instance()
        qinst.removeMapLayer(qinst.mapLayersByName(name)[0].id())
        
        iface.mapCanvas().refresh()
    
    def openSkrivWindow(self):        
#        only make instance of windows if this is None
        if self.skrivWindowInstance == None:
            self.skrivWindowInstance = QtWidgets.QDialog()
            self.ui = Ui_SkrivDialog(self.data, self.listOfEgenskaper) #instance self.v only exist after seacrh btn is pressed
            self.ui.setupUi(self.skrivWindowInstance)
            self.skrivWindowInstance.show()
            self.skrivWindowOpened = True
            
#        only shows windows again if this is allready opened
        if self.skrivWindowOpened and self.skrivWindowInstance:
            self.skrivWindowInstance.show()
            
    def onAnyFeatureSelected(self):
        self.openSkrivWindowBtn.setEnabled(True)
        
    def on_objectSizeOnLayerChange(self, value):
        layer = iface.activeLayer()
    
        renderer = layer.renderer()
    
        symbol = None #for symbol
        symbolColor = None #for symbol color
        
#        getting properties from the features already in layer
        properties = renderer.symbol().symbolLayers()[0].properties()
        
#        looping to find color key and substracting color, for later use
#        and avoid change of color when resizing the features in the current layer
        for key, val in properties.items():
            if key == 'color':
                symbolColor = val
    
        if renderer.symbol().type() == QgsSymbol.Fill:
            symbol = QgsFillSymbol.createSimple({'outline_width': value, 'color': symbolColor})
            renderer.setSymbol(symbol)
        
        if renderer.symbol().type() == QgsSymbol.Marker:
            symbol = QgsMarkerSymbol.createSimple({'size' : value, 'color': symbolColor})
            renderer.setSymbol(symbol)
            
        if renderer.symbol().type() == QgsSymbol.Line:
            symbol = QgsLineSymbol.createSimple({'line_width': value, 'color': symbolColor})
            renderer.setSymbol(symbol)
                
                
        # show the change
        layer.triggerRepaint()