from nvdbLesWrapper import AreaGeoDataParser
#from .source_skriv_window import SourceSkrivDialog
from qgis.utils import iface
from nvdbapi.nvdbapiv3 import nvdbFagdata
import threading
import time
import signal


"""def get_object_parents():

    AreaGeoDataParser.set_env('test')

    possible_objects_parents = AreaGeoDataParser.get_dataCataloge_roadObjectType_parents(88)

    print("Object can have parents:\n")
    
    for parent in possible_objects_parents:
        print(f"{parent}\n")

get_object_parents()
"""

"""

def get_selected_object_nvdbid():
    especific_field = {}
    layer = iface.activeLayer()
    selected_ids = layer.selectedFeatureIds()
    #print(selected_ids
    #print(layer.fields())
    
    for feature in layer.selectedFeatures():
        for field in feature.fields():
            if 'nvdbid' in field.name(): 
                print(f"nvdbid: {feature.attribute(field.name())}")
                print(f"Assosierte Kommentar: {feature.attribute(field.name())}")
    
    
    for feature in layer.selectedFeatures():
        for field in feature.fields():
            if 'Assosierte Kommentar' in field.name():
                layer.startEditing()
                attr_val = str(feature.attribute(field.name()))
                attr_val = "OK"
                print(attr_val)
            #print(type(field))
    layer.commitChanges()

    
get_selected_object_nvdbid()
"""


class ThreadHandling:

    def __init__(self):
        self.exit_event = threading.Event()
        self.amount_obj = nvdbFagdata(88, filter={'kommune' : 301})

    def search(self):
        self.t1 = threading.Thread(target=self.handle_thread)
        self.t1.start()

    def handle_thread(self):
        #amount_obj.filter({'fylke': int(34)})
        #amount_obj.filter({'kommune': int(3403)})
        self.amount_obj.to_records(self.exit_event)

    def interrupt_handler(self):
        print("INTERRUPT ACTIVATED")

        self.exit_event.set()



# Create an instance of the class
thread_handler = ThreadHandling()

thread_handler.search()
time.sleep(9)
t2 = threading.Thread(target=thread_handler.interrupt_handler)
t2.start()

#signal.signal(signal.SIGINT, thread_handler.interrupt_handler)

print(f"t1: thread is sill alive? {thread_handler.t1.is_alive()}")
print(f"t2: thread is sill alive? {t2.is_alive()}")







































