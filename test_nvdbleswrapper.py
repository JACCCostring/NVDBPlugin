from nvdbLesWrapper import AreaGeoDataParser


def test():
    AreaGeoDataParser.set_env('test')
    data = AreaGeoDataParser.get_datacatalog_relation_type(461, 'Belysningspunkt')
    
    print(data)
    
test()