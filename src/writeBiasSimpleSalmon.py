#!/usr/bin/python

import sqlite3 as lite
import os
import datetime

import MySQLdb

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import zipfile
import math
import numpy
import scipy.stats as stats

import subprocess
import sys


def Usage():
    print '\nwriteBiasSimpleSalmon.py forecast_file output_file'
    print '\n    forecast_file: format must be WindNinja point output format from wx model run.'
    print '    output_file: The output file name, .txt and .kmz will be appended.'
    print '\n    Writes .txtWindNinja vs. observations for mulitple timesteps.' 
    sys.exit(0)

forecast_file = None
outFile = None

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
        if forecast_file is None:
	        forecast_file = argv[i]
        elif outFile is None:
	        outFile = argv[i]
        else:
            Usage()

        i = i + 1

    if len(argv) < 3:
        print "Not enough args..."
        Usage()

#============================================================================================
#             Determine type of forecast and set fcast_start, fcast_end.
#============================================================================================
fin = open("%s" % forecast_file, 'r')
line = fin.readline()
line = fin.readline()
fcast_start = line.split(",")[4][:-4] # used in kml text
print 'Forecast start time is %s' % fcast_start
while True:
    line = fin.readline()
    if len(line) == 0: 
        break #EOF
    fcast_end = line.split(",")[4][:-4] # used in kml text
print 'Forecast end time is %s' % fcast_end
fin.close()

#============================================================================================
#  Extract averaged point data from the database.
#
#  This data is bounded by a start and end time. The data are averaged over 10 min 
#  centered at the top of the hour.
#============================================================================================

def location(plot):
    con = lite.connect('/home/natalie/DN/hires_wind/salmon_river/paul.sqlite')
    if con is None:
            if __debug__:
                print 'Failed to connect to sqlite database'
            return None
    cur = con.cursor()
    sql = """SELECT geometry
             FROM plot_location
             WHERE plot_id='%s'""" % plot
    cur.execute(sql)
    result = cur.fetchone()
    con.close()
    result[0]
    r = result[0].split(",")
    lat = r[0][(r[0].find('(')) + 1:]
    lon = r[1][:(r[0].find(')')) - 1]
    print 'lat, r[1] = ', lat, ", ", lon
    return lat, lon
    
def extract_point(timeStart, timeEnd, nominalTime):
    data_mean = list()
    con = lite.connect('/home/natalie/DN/hires_wind/salmon_river/paul.sqlite')
    cur = con.cursor()
    sql = """SELECT * FROM mean_flow_obs
              WHERE Plot_id='%s'
              AND Date_time BETWEEN '%s' AND '%s'
              AND Quality='OK'""" \
              % (plot,
              timeStart.strftime('%Y-%m-%d %H:%M:%S'),
              timeEnd.strftime('%Y-%m-%d %H:%M:%S'))
    cur.execute(sql)
    data = cur.fetchall()
    if __debug__:
        print 'Query fetched %i result(s)' % len(data)
    con.close()
    if len(data) == 0:
        print 'Query fetched no data for plot %s.' % plot
        return None
    speed = list()
    gust = list()
    direction = list()

    for i in xrange(len(data)):
        speed.append((data[i][2])*0.447) # convert to m/s
        gust.append((data[i][3])*0.447) # convert to m/s
        if data[i][6] != 'BADVANE': #only average good direction data
            direction.append(data[i][4])
    samples = numpy.array(speed)
    speed_mean = numpy.mean(samples)
    samples = numpy.array(gust)
    gust_mean = numpy.mean(samples)
    if direction != []:
        samples = numpy.array(direction)
        direction_mean = stats.morestats.circmean(samples, 360, 0)
    else:
        direction_mean = None

    # append this hour's data to the list
    data_mean.append((data[0][0], nominalTime, speed_mean, gust_mean,
                      direction_mean, data[0][5], data[0][6]))
    return data_mean

#plot = "NE2"
#lat, lon = location(plot)

#start = "2011-08-18 00:00:00"
#end = "2011-08-19 00:00:00"
#timeStart = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
#timeEnd = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
#nominalTime = "2011-08-18"
#data = extract_point(timeStart, timeEnd, nominalTime)
#print 'lat, lon = ', lat, ', ', lon
#print 'data[0][0] = ', data[0][0]
#======================================================================================


#=====================================================================================
#                  Prepare output files for writing.
#=====================================================================================

f = open("%s.txt" % outFile, 'w')
f.write('Plot,lat,lon,datetime,obs_speed(m/s),pred_speed(m/s),bias_speed(m/s),obs_dir,pred_dir,bias_dir,wx_speed(m/s),wx_bias_speed(m/s),wx_dir,wx_bias_dir\n')

#=====================================================================================
#                  Calculate biases and write files.
#=====================================================================================
fin = open("%s" % forecast_file, 'r')
line = fin.readline() #read headers
i = 0
while True:
    line = fin.readline()
    if len(line) == 0:
        print 'Reached end of forecast file. %d lines read.\n' % i 
        break #EOF
    i += 1
    plot = line.split(",")[0]
    lat = float(line.split(",")[1])
    lon = float(line.split(",")[2])
    height = float(line.split(",")[3])
    date_time = line.split(",")[4][:-4]
    u = float(line.split(",")[5])
    v = float(line.split(",")[6])
    w = float(line.split(",")[7])
    nominalTime = datetime.datetime.strptime(date_time, "%Y-%b-%d %H:%M:%S") # used in output files
    timeStart = nominalTime - datetime.timedelta(minutes = 5)
    timeEnd = nominalTime + datetime.timedelta(minutes = 5) #average over 5 min
    try:
        data = extract_point(timeStart, timeEnd, nominalTime) #extract avgs for this hour
        obs_spd = data[0][2]
        obs_dir = data[0][4]
        pred_spd = ((u*u+v*v)**0.5)
        bias_spd = pred_spd - obs_spd
        pred_dir = math.atan2(-u,-v)*180/math.pi
        if pred_dir < 0:
            pred_dir = pred_dir + 360
        bias_dir = abs(pred_dir - obs_dir)
        if bias_dir > 180:
            bias_dir = bias_dir - 180
        
        #bias_dir = pred_dir - obs_dir
        #if bias_dir > 180.0:
            #bias_dir = bias_dir - 360
        #elif bias_dir < -180.0:
            #bias_dir = bias_dir + 360
            
        u_wx = float(line.split(",")[8])
        v_wx = float(line.split(",")[9])

        wx_spd = ((u_wx*u_wx+v_wx*v_wx)**0.5)
        wx_bias_spd = wx_spd - obs_spd
        wx_dir = math.atan2(-u_wx,-v_wx)*180/math.pi
        if wx_dir < 0:
            wx_dir = wx_dir + 360
        wx_bias_dir = abs(wx_dir - obs_dir)
        if wx_bias_dir > 180:
            wx_bias_dir = wx_bias_dir - 180
        
        #wx_bias_dir = wx_dir - obs_dir
        #if wx_bias_dir > 180.0:
            #wx_bias_dir = wx_bias_dir - 360
        #elif wx_bias_dir < -180.0:
            #wx_bias_dir = wx_bias_dir + 360
        f.write('%s,%.4f,%.4f,%s,%.1f,%.1f,%.1f,%.0f,%.0f,%.0f,%.1f,%.1f,%.0f,%.0f\n' % (plot, lat, lon, date_time,
                obs_spd, pred_spd, bias_spd, obs_dir, pred_dir, bias_dir, wx_spd, wx_bias_spd, wx_dir, wx_bias_dir))

    except:
        print 'some errors, not all points written...'
        continue   
            
fin.close()
f.close()
print '%s.txt written.' % outFile




