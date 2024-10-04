# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'nvdb_endringsset_status_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QTextEdit
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

import xml.etree.ElementTree as ET
from qgis.PyQt import uic
import requests, io
import os


# import inspect

# from .more_window import Ui_MoreDialog

FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nvdb_endringsset_status_window.ui'))
    
class Ui_windowProgress(BASE_CLASS, FORM_CLASS):
    
    def __init__(self, endringsett):
        super().__init__()
        
        self.setupUi(self)

        self.endringsett = endringsett

#        starting up default UI values
        tableProgress_column_labels = {'nvdbid', 'navn'}
        
        self.tableProgress.setColumnCount(2)
        
        self.tableProgress.setHorizontalHeaderLabels(tableProgress_column_labels)
        self.tableProgress.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableProgress.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # populating table widget when starting windows
        self.populate_table(self.endringsett)
        
        self.statusText.setReadOnly(True)
        
        #        connecting signals
        self.hideBtn.clicked.connect(lambda: self.hide()) #hide window
        self.tableProgress.clicked.connect(self.itemClicked) #checking status when item clicked
        self.cancelBtn.clicked.connect(self.cancell_endringssett) #cancell sent, endringsett if it's not sent yet'


    def populate_table(self, endringsetts):
        row = 0

        for endringsett in endringsetts:
            # for item in endringsett:
            for key, value in endringsett.items():
                if key == 'current_nvdbid':
                    self.tableProgress.setRowCount(row + 1)
                        
                    self.tableProgress.setItem(row, self.getIndexFieldFromColumn('nvdbid'), QTableWidgetItem(str(value)))
                    
                if key == 'vegobjekt_navn':
                    self.tableProgress.setItem(row, self.getIndexFieldFromColumn('navn'), QTableWidgetItem(str(value)))
            
            row += 1
    
    def getIndexFieldFromColumn(self, columnName):
        column_index = 0 #0 field by default
        columnText = ''
        
        for _column in range(0, self.tableProgress.columnCount()):
            columnText = self.tableProgress.horizontalHeaderItem(_column).text()
            
            if columnName in columnText:
                column_index = _column
        
        return column_index
        
    def getTextFieldFromColumnIndex(self, item, columnName):
        row = item.row()
        column_index = 0 #0 field by default
        
        for _column in range(0, self.tableProgress.columnCount()):
            columnText = self.tableProgress.horizontalHeaderItem(_column).text()
            
            if columnName in columnText:
                column_index = _column
        
        field_text = self.tableProgress.item(row, column_index).text()
        
        return field_text
        
    def check_status(self, url, token):
        header = {
            'X-Client': 'QGIS Skriv',
            'Type-Content': 'application/xml',
            'Authorization': token
        }
        
        response = requests.get(url, headers = header)
        
        # print('nvdb_endringsset_status_windows: ', response.text)

        #if response is not ok, then we just clear all the items
        if response.ok != True:
            print("Response in nvdb_endringsett_status::check_status not ok: ",response.text)
            return
            
            if self.tableProgress.rowCount() > 0:
                self.tableProgress.clear()
                self.endringsett.clear()

        if response.ok:
            file_stream = io.StringIO(response.text)
            
            try:
                tree = ET.parse(file_stream)
                
                root = tree.getroot()
                
                concat_str = str('')
                show_melding = str('')
         
                for element in root.findall('.//'):
                    if 'vegobjekt' in element.tag:
                        
                        for melding in element.findall('.//'):
                            if 'melding' in melding.tag:
                                show_melding += f'<p style="color:blue">{melding.text}</p>'
                    
                    if 'fremdrift' in element.tag:
                        if 'BEHANDLES' or 'UTFØRT_OG_ETTERBEHANDLET' in element.text:
                            concat_str += f'<p style="color:green">{element.text}</p>'
                            
                        if 'AVVIST' in element.text:
                            concat_str = f'<p style="color:red">{element.text}</p>'
                
                # if concat_str:
                #     self.statusText.setText(concat_str + show_melding)
                    
            except ET.ParseError:
                concat_str = f'<p style="color:red">prøver igjen</p>'
                show_melding = ''
                
            if concat_str:
                self.statusText.setText(concat_str + show_melding)
        
    def cancell_endringssett(self):
        if self.tableProgress.rowCount() > 0:
            self.send_cancell_post(self.current_item['endringsett_id'], self.current_item['token'])
    
    def send_cancell_post(self, url, token):
        header = {
            'X-Client': 'QGIS Skriv',
            'Type-Content': 'application/xml',
            'Authorization': token
        }
        
        response = requests.post(url + '/kanseller', headers = header)
        
        # if response.ok:
        msg = 'endringssett er kansellert !'
            
        self.statusText.setText(f'<p style="color:green">{msg}</p>')
            
        file_stream = io.StringIO(response.text)
        tree = ET.parse(file_stream)
        root = tree.getroot()
            
        for tag in root.findall('.//'):
            if 'message' in tag.tag:
                self.statusText.setText(f'<p style="color:red">{tag.text}</p>')

    def getClicked_NVDBID(self):
        nvdbid = None
        
        for item in self.tableProgress.selectedItems():
            if item.isSelected():
                nvdbid = self.getTextFieldFromColumnIndex(item, 'nvdbid')
        
        return nvdbid
    
    def isVegObjektThere(self):
        nvdbid = self.getClicked_NVDBID()
        
        for endring in self.endringsett:
            for key, value in endring.items():
                if key == 'current_nvdbid':
                    if str(value) == nvdbid:
                        self.current_item = endring
                        
                        return True
        
        return False
        
    def itemClicked(self):
        if self.isVegObjektThere():
            # print('current selected item: ', self.current_item['status_after_sent'])
            self.check_status(self.current_item['status_after_sent'], self.current_item['token'])
