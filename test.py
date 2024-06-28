from nvdbLesWrapper import AreaGeoDataParser
#from .source_skriv_window import SourceSkrivDialog
from qgis.utils import iface


def get_object_parents():

    AreaGeoDataParser.set_env('test')

    possible_objects_parents = AreaGeoDataParser.get_dataCataloge_roadObjectType_parents(88)

    print("Object can have parents:\n")
    
    for parent in possible_objects_parents:
        print(f"{parent}\n")

get_object_parents()


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













































