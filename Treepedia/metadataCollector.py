
# This function is used to collect the metadata of the GSV panoramas based on the sample point shapefile

# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT

def GSVpanoMetadataCollector(samplesFeatureClass,num,ouputTextFolder):
    '''
    This function is used to call the Google API url to collect the metadata of
    Google Street View Panoramas. The input of the function is the shpfile of the create sample site, the output
    is the generate panoinfo matrics stored in the text file

    Parameters:
        samplesFeatureClass: the shapefile of the create sample sites
        num: the number of sites proced every time
        ouputTextFolder: the output folder for the panoinfo

    '''

    import urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse
    import xmltodict
    import io
    import math
    from osgeo import ogr, osr
    import time
    import os,os.path
    import json
    import streetview

    if not os.path.exists(ouputTextFolder):
        os.makedirs(ouputTextFolder)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    if driver is None:
        print('Driver is not available.')

    # change the projection of shapefile to the WGS84
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print('Could not open %s' % (samplesFeatureClass))

    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(sourceProj, targetProj)

    # loop all the features in the featureclass
    feature = layer.GetNextFeature()
    featureNum = layer.GetFeatureCount()
    batch = math.ceil(featureNum/num)

    for b in range(batch):
        # for each batch process num GSV site
        start = b*num
        end = (b+1)*num
        if end > featureNum:
            end = featureNum

        ouputTextFile = 'Pnt_start%s_end%s.txt'%(start,end)
        ouputGSVinfoFile = os.path.join(ouputTextFolder,ouputTextFile)

        # skip over those existing txt files
        if os.path.exists(ouputGSVinfoFile):
            continue

        time.sleep(1)

        key = get_keys()  #Input Your Key here

        with open(ouputGSVinfoFile, 'w') as panoInfoText:
            # process num feature each time
            for i in range(start, end):
                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()

                # trasform the current projection of input shapefile to WGS84
                #WGS84 is Earth centered, earth fixed terrestrial ref system
                geom.Transform(transform)
                lat = geom.GetX()
                lon = geom.GetY()

                # get the meta data of panoramas
                urlAddress = 'https://maps.googleapis.com/maps/api/streetview/metadata?location=%s,%s&key=%s'%(lat,lon,key)

                time.sleep(0.01)
                # the output result of the meta data is a json object
                metaDatajson = urllib.request.urlopen(urlAddress)
                metaData = metaDatajson.read()
                data = json.loads(metaData)
                #print(data)

                # in case there is not panorama in the site, continue
                if data['status'] != 'OK':
                    continue
                else:
                    panoDate, panoId, panoLat, panoLon = getPanoItems(data)

                    print(('The coordinate (%s,%s), panoId is: %s, panoDate is: %s'%(panoLon, panoLat, panoId, panoDate)))
                    lineTxt = 'panoID: %s panoDate: %s longitude: %s latitude: %s\n'%(panoId, panoDate, panoLon, panoLat)
                    panoInfoText.write(lineTxt)

        panoInfoText.close()

def getPanoItems(data):
    # get the meta data of the panorama
    panoDate = data.get('date') # Sometimes the date is not available exception
    panoId = data['pano_id']
    panoLat = data['location']['lat']
    panoLon = data['location']['lng']
    return panoDate, panoId, panoLat, panoLon

def get_keys():
    # Function to get the keys from main keys file
    os.chdir("./")
    key_file = os.path.join(os.getcwd(), 'keys.txt')

    lines = open(key_file,"r")
    keylist = []
    for line in lines:
        key = line.rstrip()
        keylist.append(key)
    lines.close()

    #print ('The key list is:=============', keylist)
    return keylist[0]

# ------------Main Function -------------------
if __name__ == "__main__":
    import os, os.path

    root = '../spatial-data'
    inputShp = os.path.join(root,'GLSG_small_out.shp')
    outputTxt = root

    GSVpanoMetadataCollector(inputShp,1000,outputTxt)
