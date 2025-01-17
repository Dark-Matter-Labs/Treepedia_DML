
# This program is used to calculate the green view index based on the collecte metadata. The
# Object based images classification algorithm is used to classify the greenery from the GSV imgs
# in this code, the meanshift algorithm implemented by pymeanshift was used to segment image
# first, based on the segmented image, we further use the Otsu's method to find threshold from
# ExG image to extract the greenery pixels.

# For more details about the object based image classification algorithm
# check: Li et al., 2016, Who lives in greener neighborhoods? the
# distribution of street greenery and it association with residents'
# socioeconomic conditions in Hartford, Connectictu, USA

# This program implementing OTSU algorithm to chose the threshold automatically
# For more details about the OTSU algorithm and python implmentation
# cite:
# http://docs.opencv.org/trunk/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html


# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT
# First version June 18, 2014

import time
from PIL import Image
import numpy as np
import requests
import sys
from urllib.parse import urlencode
import pymeanshift as pms


def graythresh(array, level):
    '''array: is the numpy array waiting for processing
    return thresh: is the result got by OTSU algorithm
    if the threshold is less than level, then set the level as the threshold
    by Xiaojiang Li
    '''

    np.seterr(divide='ignore', invalid='ignore')

    maxVal = np.max(array)
    minVal = np.min(array)

    # if the inputImage is a float of double dataset then we transform the data
    # in to byte and range from [0 255]
    if maxVal <= 1:
        array = array * 255
    elif maxVal >= 256:
        array = np.int((array - minVal) / (maxVal - minVal))

    # turn the negative to natural number
    negIdx = np.where(array < 0)
    array[negIdx] = 0

    # calculate the hist of 'array'
    dims = np.shape(array)
    hist = np.histogram(array, range(257))
    P_hist = hist[0] * 1.0 / np.sum(hist[0])

    omega = P_hist.cumsum()

    temp = np.arange(256)
    mu = P_hist * (temp + 1)
    mu = mu.cumsum()

    n = len(mu)
    mu_t = mu[n - 1]

    sigma_b_squared = (mu_t * omega - mu)**2 / (omega * (1 - omega))

    # try to found if all sigma_b squrered are NaN or Infinity
    indInf = np.where(sigma_b_squared == np.inf)

    CIN = 0
    if len(indInf[0]) > 0:
        CIN = len(indInf[0])

    maxval = np.max(sigma_b_squared)

    IsAllInf = CIN == 256
    if IsAllInf != 1:
        index = np.where(sigma_b_squared == maxval)
        idx = np.mean(index)
        threshold = (idx - 1) / 255.0
    else:
        threshold = level

    if np.isnan(threshold):
        threshold = level

    return threshold


def VegetationClassification(Img):
    '''
    This function is used to classify the green vegetation from GSV image,
    This is based on object based and otsu automatically thresholding method
    The season of GSV images were also considered in this function
        Img: the numpy array image, eg. Img = np.array(Image.open(StringIO(response.content)))
        return the percentage of the green vegetation pixels in the GSV image

    By Xiaojiang Li
    '''

    # use the meanshift segmentation algorithm to segment the original GSV
    # image
    (segmented_image, labels_image, number_regions) = pms.segment(
        Img, spatial_radius=6, range_radius=7, min_density=40)

    I = segmented_image / 255.0

    red = I[:, :, 0]
    green = I[:, :, 1]
    blue = I[:, :, 2]

    # calculate the difference between green band with other two bands
    green_red_Diff = green - red
    green_blue_Diff = green - blue

    ExG = green_red_Diff + green_blue_Diff
    diffImg = green_red_Diff * green_blue_Diff

    redThreImgU = red < 0.6
    greenThreImgU = green < 0.9
    blueThreImgU = blue < 0.6

    shadowRedU = red < 0.3
    shadowGreenU = green < 0.3
    shadowBlueU = blue < 0.3
    del red, blue, green, I

    greenImg1 = redThreImgU * blueThreImgU * greenThreImgU
    greenImgShadow1 = shadowRedU * shadowGreenU * shadowBlueU
    del redThreImgU, greenThreImgU, blueThreImgU
    del shadowRedU, shadowGreenU, shadowBlueU

    greenImg3 = diffImg > 0.0
    greenImg4 = green_red_Diff > 0
    threshold = graythresh(ExG, 0.1)

    if threshold > 0.1:
        threshold = 0.1
    elif threshold < 0.05:
        threshold = 0.05

    greenImg2 = ExG > threshold
    greenImgShadow2 = ExG > 0.05
    greenImg = greenImg1 * greenImg2 + greenImgShadow2 * greenImgShadow1
    del ExG, green_blue_Diff, green_red_Diff
    del greenImgShadow1, greenImgShadow2

    # calculate the percentage of the green vegetation
    greenPxlNum = len(np.where(greenImg != 0)[0])
    greenPercent = greenPxlNum / (400.0 * 400) * 100
    del greenImg1, greenImg2
    del greenImg3, greenImg4

    return greenPercent


# using 18 directions is too time consuming, therefore, here I only use 6 horizontal directions
# Each time the function will read a text, with 1000 records, and save the
# result as a single TXT
def GreenViewComputing_ogr_6Horizon(GSVinfoFolder, outTXTRoot, greenmonth):
    """
    This function is used to download the GSV from the information provide
    by the gsv info txt, and save the result to a shapefile

    Required modules: numpy, requests, and PIL

        GSVinfoTxt: the input folder name of GSV info txt
        outTXTRoot: the output folder to store result green result in txt files
        greenmonth: a list of the green season, greenmonth = ['05','06','07','08','09']

    """

    # read the Google Street View API key files, you can also replace these
    # keys by your own

    # set a series of heading angle
    headingArr = 360 / 6 * np.array([0, 1, 2, 3, 4, 5])

    # number of GSV images for Green View calculation, in my original Green
    # View View paper, I used 18 images, in this case, 6 images at different
    # horizontal directions should be good.
    numGSVImg = len(headingArr) * 1.0
    pitch = 0

    # create a folder for GSV images and grenView Info
    if not os.path.exists(outTXTRoot):
        os.makedirs(outTXTRoot)

    # the input GSV info should be in a folder
    if not os.path.isdir(GSVinfoFolder):
        print('You should input a folder for GSV metadata')
        return
    else:
        allTxtFiles = os.listdir(GSVinfoFolder)
        for txtfile in allTxtFiles:
            if not txtfile.endswith('.txt'):
                continue

            txtfilename = os.path.join(GSVinfoFolder, txtfile)
            panoIDLst, panoDateLst, panoLonLst, panoLatLst = get_pano_lists_from_file(
                txtfilename, greenmonth)

            # the output text file to store the green view and pano info
            gvTxt = 'GV_' + os.path.basename(txtfile)
            GreenViewTxtFile = os.path.join(outTXTRoot, gvTxt)

            # check whether the file already generated, if yes, skip.
            # Therefore, you can run several process at same time using this
            # code.
            print("Processing", GreenViewTxtFile)
            if os.path.exists(GreenViewTxtFile):
                print("File already exists")
                continue

            # write the green view and pano info to txt
            with open(GreenViewTxtFile, "w") as gvResTxt:
                for i in range(len(panoIDLst)):
                    panoDate = panoDateLst[i]
                    panoID = panoIDLst[i]
                    lat = panoLatLst[i]
                    lon = panoLonLst[i]

                    # calculate the green view index
                    greenPercent = 0.0

                    for heading in headingArr:
                        print("Heading is: ", heading)

                        # using different keys for different process, each key
                        # can only request 25,000 imgs every 24 hours
                        URL = get_api_url(panoID, heading, pitch)

                        # classify the GSV images and calcuate the GVI
                        try:
                            im = retreive_image(URL, panoID, heading)
                            percent = VegetationClassification(im)
                            greenPercent = greenPercent + percent

                        # if the GSV images are not download successfully or
                        # failed to run, then return a null value
                        except BaseException:
                            print("Unexpected error:", sys.exc_info())
                            greenPercent = -1000
                            break

                    # calculate the green view index by averaging six percents
                    # from six images
                    greenViewVal = greenPercent / numGSVImg
                    print(
                        'The greenview: %s, pano: %s, (%s, %s)' %
                        (greenViewVal, panoID, lat, lon))

                    # write the result and the pano info to the result txt file
                    lineTxt = 'panoID: %s panoDate: %s longitude: %s latitude: %s, greenview: %s\n' % (
                        panoID, panoDate, lon, lat, greenViewVal)
                    gvResTxt.write(lineTxt)


def get_api_url(panoID, heading, pitch):
    params = {
        "size": "400x400",
        "pano": panoID,
        "fov": 60,
        "heading": heading,
        "pitch": pitch,
        "sensor": "false",
        "key": config.gcloud_key,
        "source": "outdoor"
    }
    URL = "http://maps.googleapis.com/maps/api/streetview?" + urlencode(params)
    return URL


def get_api_image(url, img_path):
    response = requests.get(url, stream=True)
    image = Image.open(response.raw)

    save_img_to_local(image, img_path)

    # let the code to pause by 1s, in order to not go over
    # data limitation of Google quota
    time.sleep(0.005)

    return np.array(image)


def save_img_to_local(image, path):
    # Saving the images to a local path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)


def retreive_image(URL, panoID, heading):
    ''' A function that retreives an image it first cheks if it exists locally,
     if it doesn't it fetches the image from the API, save it and return it'''

    img_path = config.GVIfile['images'] + \
        str(panoID) + '_' + str(heading) + '.jpg'

    # If the images exists locally it retreives it
    if os.path.isfile(img_path):
        return np.array(Image.open(img_path))
    else:
        return get_api_image(URL, img_path)


def get_pano_lists_from_file(txtfilename, greenmonth):
    lines = open(txtfilename, "r")

    # create empty lists, to store the information of panos,and remove
    # duplicates
    panoIDLst = []
    panoDateLst = []
    panoLonLst = []
    panoLatLst = []

    # loop all lines in the txt files
    for line in lines:
        metadata = line.split(" ")
        panoID = metadata[1]
        panoDate = metadata[3]
        month = panoDate[-2:]
        lon = metadata[5]
        lat = metadata[7][:-1]

        # in case, the longitude and latitude are invalide
        if len(lon) < 3:
            continue

        # only use the months of green seasons
        if month not in greenmonth:
            continue
        if panoID in panoIDLst:
            continue
        else:
            panoIDLst.append(panoID)
            panoDateLst.append(panoDate)
            panoLonLst.append(lon)
            panoLatLst.append(lat)

    lines.close()

    return panoIDLst, panoDateLst, panoLonLst, panoLatLst


# ------------------------------Main function-------------------------------
if __name__ == "__main__":

    import os
    import os.path
    import config

    os.chdir(config.root_dir)
    root = os.getcwd()
    GSVinfoRoot = os.path.join(root, "")
    outputTextPath = os.path.join(root, config.GVIfile['data'])
    greenmonth = config.greenmonth

    GreenViewComputing_ogr_6Horizon(GSVinfoRoot, outputTextPath, greenmonth)
