from PyQt5.QtCore import pyqtSignal, QDateTime, QDate


def test():
    
    date = QDateTime().currentDateTime()
    date2 = QDate()
    
    cu = date2.currentDate()
    
    if isinstance(date, QDateTime):
        print('equal date')
    
    if isinstance(date2, (QDate, QDateTime)):
        print('equal date2')
        
    print('type', type( date ))
    print('crr date', type(cu))
    
test()