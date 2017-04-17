#!/usr/bin/env python

import subprocess
import os
import sys

import datetime
import urllib2
import zipfile

import math

def Usage():
    print '\nextractWind.py lat lon start_time end_time [-f path_to_zip_files]'
    print '\n    Extracts wind speed and direction at 10 m using gdallocation info.'
    print '\n    If -f is not specified, attempts to fetch forecast(s) from NCEP page.\n'
    print '\n    Time format: 2012-06-15T00:00:00\n'
    sys.exit(0)

lat = None
lon = None
start_time = None
end_time = None
pathToZipFiles = None

#=============================================================================
#             Parse command line options.
#=============================================================================

if __name__ == '__main__':
    argv = sys.argv
    if argv is None:
        sys.exit(0)   

    i = 1

    while i < len(argv):
        arg = argv[i]
        if arg == '-f':
            i = i + 1
            pathToZipFiles = argv[i]
        elif lat is None:
            lat = float(argv[i])
        elif lon is None:
            lon = float(argv[i])
        elif start_time is None:
            start_time = argv[i]
        elif end_time is None:
	        end_time = argv[i]
        else:
            Usage()

        i = i + 1

    if len(argv) < 3:
        print "Not enough args..."
        Usage()

start = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
end = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')

#===============================================================================
#     Make a list of datetimes.
#===============================================================================
def getTimeList():
    hours = int((end - start).total_seconds()/60/60) #total hours requested
    for hour in xrange(hours):
        theTime = start + datetime.timedelta(hours=hour)
        if theTime.hour in [3, 6, 9, 12, 15, 18, 24]:
            timeList.append(theTime) # append in 3-hr increments


#===============================================================================
#     Fetch winds for files in a local zipfile.
#===============================================================================
def getWindFromZip():
    for time in timeList: # set Y,M,D,H
        year = str(time.year)
        month = str(time.month)
        if len(month) == 1:
            month = '0' + month
        day = str(time.day)
        if len(day) == 1:
            day = '0' + day
        hour = str(time.hour)
        if len(hour) == 1:
            hour = '0' + hour
        namName = 'nam_218_%s%s%s_0000_0%s.grb' % (year, month, day, hour)
        zippedFile = pathToZipFiles + '/nam_%s%s%s.zip' % (year, month, day)
        zf = zipfile.ZipFile(zippedFile, "r")
        for fcastFile in zf.namelist(): 
            if fcastFile == namName:
                print 'fcastFile = ', namName
                tempFile = open(fcastFile, 'wb') #extract to temp file on disk for gdal
                tempFile.write(zf.read(fcastFile))
                tempFile.close()
                extractWind(fcastFile)
                os.remove(fcastFile)
        zf.close()

#===============================================================================
#     Make a list of urls to fetch forecasts.
#===============================================================================
def getWindFromUrl():
    for time in timeList:
        year = str(time.year)
        month = str(time.month)
        if len(month) == 1:
            month = '0' + month
        day = str(time.day)
        if len(day) == 1:
            day = '0' + day
        hour = str(time.hour)
        if len(hour) == 1:
            hour = '0' + hour
        url = 'http://nomads.ncdc.noaa.gov/data/meso-eta-hi/%s%s/%s%s%s/nam_218_%s%s%s_0000_0%s.grb'\
               % (year, month, year, month, day, year, month, day, hour)
        #url = 'http://nomads.ncdc.noaa.gov/data/meso-eta-hi/201206/20120615/nam_218_20120615_0000_003.grb'
        urlList.append(url)
    for url in urlList:
        print 'url = ', url
        print 'Downloading the forecast...'
        fcastFile = fetchForecast(url)
        extractWind(fcastFile)
        os.remove(fcastFile)
    

#===============================================================================
#     Fetch forecasts. 
#     NO CHECKS FOR CONNECTION, DATA EXISTENCE, ETC...
#===============================================================================

def fetchForecast(url):
    fcastFile = 'nam.grb'
    fin = urllib2.urlopen(url)    
    output = open(fcastFile,'wb')
    output.write(fin.read())
    output.close()
    return fcastFile
        
#===============================================================================
#     Fetch U10, V10 from forecast.
#===============================================================================
def extractWind(fcastFile):
    data = subprocess.Popen(["gdallocationinfo -valonly -b 9 -b 10 -wgs84 %s"\
           " %.9f, %.9f" % (fcastFile, lon, lat)], shell = True, stdout=subprocess.PIPE)
    out, err = data.communicate()
    if out == '':
        print "Warning: gdallocation info returned no data. Is the lat/long off the grid?"
        sys.exit(0)
    out = out.split('\n')
    u10 = float(out[0])
    v10 = float(out[1])
    print 'U10, V10 = ', out[0] + ', ' + out[1]
    speed = ((u10*u10+v10*v10)**0.5)
    direction = math.atan2(-u10,-v10)*180/math.pi
    if direction < 0:
        direction += 360
    speedList.append(speed)
    directionList.append(direction)


speedList = list()
directionList = list()
timeList = list()
urlList = list()

getTimeList()

#====== fetch winds ===================
if pathToZipFiles is None: 
    getWindFromUrl() #on the fly
else:
    getWindFromZip() #from locally stored forecasts
print 'fetched speeds     = ', speedList
print 'fetched directions = ', directionList

#====== write output file ===============================
outFile = 'wind.txt'
f = open(outFile, 'w')
f.write('datetime,lat,lon,speed(m/s),direction\n')
for i, v in enumerate(speedList):
    f.write('%s,%.4f,%.4f,%.1f,%.0f\n' % (timeList[i], lat, lon, speedList[i], directionList[i]))
f.close()
print 'extractWind done! Output was written to %s.' % outFile



