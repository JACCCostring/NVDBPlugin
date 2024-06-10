from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore
from qgis.PyQt import uic
from PyQt5.QtWidgets import QApplication

import os
import inspect

# from .more_window import Ui_MoreDialog

FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'more_window.ui'))

class SourceMoreWindow(BASE_CLASS, FORM_CLASS):
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        
        self.click_btn.clicked.connect(self.print_method)

    def print_method(self):
        print('clicking ...')
