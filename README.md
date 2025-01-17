# DML

This repository is part on an exploratory project for Trees as Infrastructure, or TreesAI with the intention to use the TreePedia methodology for the city of Glasgow.
A version of the results can be found on this [interactive map](https://api.mapbox.com/styles/v1/axeln78/ckq9lilv206hb17piyvfttnl9.html?fresh=true&title=view&access_token=pk.eyJ1IjoiYXhlbG43OCIsImEiOiJja3A2eWd6eW4yOTB6MnZtd2dlZTl0b3I5In0.3_LCJxYIa8P4K-m2Jsyp5Q)

Most of the original code has been updated to work in python 3.X based on the previous work of https://github.com/y26805/Treepedia_Public
Additional features have been added to clean and simplify the overall codebase.

## Google Street View Keys

A functioning Google Cloud Services key is needed to retreive the Google Street View images. Therefore, make sure you have a working account with a billings account associated with the 'google street view API' enabled. Please make sure that the keys that you are using are and stay private.

## Dependencies

```# required for Matplotlib
brew install pkg-config freetype 

# required for Fiona
brew install gdal 
pip3 install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}')

# install dependency of PyMeanShift
pip3 install numpy==1.18.3

# download PyMeanShift (not available on PIP) and install
git clone https://github.com/fjean/pymeanshift.git
cd pymeanshift
sudo python setup.py install
cd ../

# clone Treepedia repository and install remaining dependencies using pip
git clone https://github.com/y26805/Treepedia_Public.git
cd Treepedia_Public
pip3 install -r requirements.txt 
```

# Treepedia
Developed by the MIT [Senseable City Lab](https://senseable.mit.edu/), *Treepedia* aims to raise a proactive awareness of urban vegetation improvement, using computer vision techniques applied to Google Street View images. Our focus is on street trees: Treepedia doesn't map parks, as GSV doesn't venture into them as it does on average streets.

*Treepedia* measures and maps the amount of vegetation cover along a city's streets by computing the Green View Index (GVI) on Google Street View (GSV) panoramas. This method considers the obstruction of tree canopies and classifies the images accordingly. The GVI presented here is on a scale of 0-100, showing the percentage of canopy coverage of a particular location. Explore the maps on the [*Treepedia*](http://senseable.mit.edu/treepedia/) website to see how the GVI changes across a city, and how it compares across cities and continents.

The following repo provides a <a href="https://github.mit.edu/abdulhai/Treepedia/wiki/Analyze-Your-City"> library to implement the GVI computation</a> for a city or region defined by a boundary shapefile, given that GSV imagery is available for the street network within it. It also includes documentation of the workflow of the project so that stakeholders, municipalities, researchers or public alike may run the analysis for their cities. We will continue to grow the *Treepedia* database to span cities all over the globe. What does your green canopy look like? If you'd like to answer this question please install this python library and run the analysis for your area. 

If you are a government, researcher or stakeholder that has used this library to compute the GVI for your city and would like us to include a mapping of it on the *Treepedia* website, please contact us at: senseable-trees@mit.edu

<br />

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/img.jpg">
</p>

# Workflow 

The project has the following workflow:

## Step 1: Point Sampling on Street Network of City 
With the street network and boundary shapefile for your city as input, a shapefile containing points every 20m (which can be changed depending on the size of the city) will be generated to be fed into the Google API to retrieve Google Street View Images. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img2.jpg">
</p>

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img1.jpg">
</p>

Note that spatial files must be in the projected WGS84 system.

Example:
You can just run the code of "1.createPoints.py" 

python 1.createPoints.py

In the example, I use Cambridge as example. At the buttom of the code, you can specify the input shapefile of the street map, the minimum distance for sampling, and the number of the output shapefile for your cities.



## Step 2: Metadata containing GSV panoID's

With the shapefile as input, metadata containing the panoID, panoDate, latitude, longitude and tilt specifications for the image will be stored in textfiles to be later used to calculate the Green View Index. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img3.jpg">
</p>

Example:
You can just run the code of "2.metadataCollector.py"

python 2.metadataCollector.py

The input of this code is created sample site shapefile. In the example, I use Cambridge20m.shp in the sample-spatialdata folder. You can generate your own sample sites based on the createPnt.py. At the buttom of the code, you can specify different sample site file. The batch size is 1000, which means the code will save metadata of every 1000 point to a txt file.



## Step 3: GVI Calculation of points with final shapefile display 
Using Otsu's method and the pymeanshift package, the Green View Index is computed for all 6 images at each sampling point; for each sampling point the GVI values are then averaged to provide a single GVI value for every point along the street network. Finally, a shapefile will be generated containing all attributes, including the GVI, of the points on the street network. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img4.jpg">
</p>

Example:

You can just run the code of "3.GreenView_Calculate.py"

python 3.GreenView_Calculate.py

The input of this code is the collected metadata of GSV. By reading the metadat, this code will collect GSV images and segmente the greenery, and calculate the green view index. Considering those GSV images captured in winter are leafless, thiwh are not suitable for the analysis. You also need to specific the green season, for example, in Cambridge, the green months are May, June, July, August, and September.

You can open several process to run this code simutaniously, because the output will be saved as txt files in folder. If the output txt file is already there, then the code will move to the next metadata txt file and generate the GVI for next 1000 points.

After finishing the computing, you can run the code of "4.Greenview2Shp.py", and save the result as shapefile, if you are more comfortable with shapefile.


# Dependencies
  * Pyshiftmean package
  * Numpy
  * GDAL
  * PIL
  * Shapely
  * Fiona
  * xmltodict 
  * Python (2.7)

# Contributors
Axel Nilsson in the Dark Matter Laboratories coding crew

Original project from MIT:
  Project Co-Leads: Xiaojiang Li and Ian Seiferling
  Researchers: Bill Cai, Marwa Abdulhai
