
# This function is used to collect the metadata of the GSV panoramas based on the sample point shapefile

# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT
import urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse
import io
import math
from osgeo import ogr, osr
import time
import os,os.path
import json
import streetview
import time
from datetime import datetime

def GSVpanoMetadataCollector(samplesFeatureClass,num,ouputTextFolder, greenmonth):
    '''
    This function is used to call the Google API url to collect the metadata of
    Google Street View Panoramas. The input of the function is the shpfile of the create sample site, the output
    is the generate panoinfo matrics stored in the text file

    Parameters:
        samplesFeatureClass: the shapefile of the create sample sites
        num: the number of sites proced every time
        ouputTextFolder: the output folder for the panoinfo

    '''



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

        time.sleep(0.1)

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
                print(data)

                # in case there is not panorama in the site, continue
                if data['status'] != 'OK':
                    continue
                else:
                    panoDate, panoId, panoLat, panoLon = getPanoItems(data)

                    # Check if the Pano corresponds to the right time of year
                    if check_pano_month_in_greenmonth(panoDate, greenmonth) is False:
                        panoLst = streetview.panoids(lon=lon, lat=lat)
                        sorted_panoList = sort_pano_list_by_date(panoLst)
                        if not sorted_panoList:
                            print(" No alternative panorama found ")
                            continue
                        else:
                            panoDate, panoId, panoLat, panoLon = get_next_pano_in_greenmonth(sorted_panoList, greenmonth)

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

def check_pano_month_in_greenmonth(panoDate, greenmonth):
    month = panoDate[-2:]
    return month in greenmonth

def sort_pano_list_by_date(panoLst):
    def func(x):
    # Classify the pano list from closest to farthest in time
        if 'year'in x:
            return datetime(year=x['year'], month=x['month'], day=1)
        else:
            return datetime(year=1, month=1, day=1)
    panoLst.sort(key=func, reverse=True)
    return panoLst

def get_next_pano_in_greenmonth(panoLst, greenmonth):
    greenmonth_int = [int(month) for month in greenmonth]



    for pano in panoLst:
        if 'month' not in pano.keys():
            continue
        month = pano['month']
        pano_year = pano['year']
        if month in greenmonth_int:
            return get_pano_items_from_dict(pano)

    print(f"No pano with greenmonth {greenmonth} found. ")
    print("Returning info of latest pano")
    print("Numbers of available panoramas:",len(panoLst))
    return get_pano_items_from_dict(panoLst[0])

def get_pano_date_str(panoMonth, panoYear):
    return str(panoYear) + '-' + str(panoMonth).zfill(2)

def get_pano_items_from_dict(pano):
    panoDate = get_pano_date_str(pano['month'], pano['year'])
    panoId = pano['panoid']
    panoLat = pano['lat']
    panoLon = pano['lon']
    return panoDate, panoId, panoLat, panoLon

def get_keys():

    return config.gcloud_key

# ------------Main Function -------------------
if __name__ == "__main__":
    import os, os.path
    import config

    root = config.root_dir
    inputShp = os.path.join(root,config.shapefile['dotted'])
    outputTxt = root

    # Add the Green Months
    greenmonth = config.greenmonth

    GSVpanoMetadataCollector(inputShp,1000,outputTxt, greenmonth)
