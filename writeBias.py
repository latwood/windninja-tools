#!/usr/bin/python

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

import Image
import ImageDraw


def Usage():
    print '\nwriteBias.py forecast_file [-i initialization_plots_file] output_file'
    print '\n    forecast_file: format must be WindNinja point output format (point or wx format).'
    print '    initialization_plots_file: Plots to omit; written by writeWxStationFile.py'
    print '    output_file: The output file name, .txt and .kmz will be appended.'
    print '\n    Writes .txt and .kmz of WindNinja vs. observations aggregated over mulitple timesteps.' 
    sys.exit(0)

forecast_file = None
initialization_plots_file = None
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
        if arg == '-i':
            i = i + 1
            initialization_plots_file = argv[i]
        elif forecast_file is None:
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
try:
    if line.split(",")[10] == 'wx_w\n':
        initType = 'wxModel'
        print 'Detected wx model initialization.'
except:
    initType = 'point' #using point also for 2d wx runs
    print 'Detected point initialization.'
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

def extract_point(timeStart, timeEnd, nominalTime):
    data_mean = list()
    connection = MySQLdb.connect(host = 'localhost', user = 'bigbutte',
                     db = 'BIG_BUTTE', unix_socket = '/var/run/mysqld/mysqld.sock')
    cursor = connection.cursor()
    sql = """SELECT * FROM MEAN_FLOW_OBS
              WHERE Plot_id='%s'
              AND Date_time BETWEEN '%s' AND '%s'
              AND Quality='OK'""" \
              % (plot,
              timeStart.strftime('%Y-%m-%d %H:%M:%S'),
              timeEnd.strftime('%Y-%m-%d %H:%M:%S'))
    cursor.execute(sql)
    data = cursor.fetchall()
    if __debug__:
        print 'Query fetched %i result(s)' % len(data)
    connection.close()
    if len(data) == 0:
        print 'Query fetched no data for plot %s.' % plot
        return None
    # average data for current hour
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
    

#=============================================================================
#          Create bias map kml.
#=============================================================================
def create_kml(plot, lat, lon, bias_spd, obs_spd, pred_spd, obs_dir, pred_dir, bias_dir):
    if plot in omitPlots: #if it's an initialization point, use a flag
        icon = 'wx_station.png'
    else: # otherwise create the icon based on speed/dir bias
        image = Image.new('RGBA', (100, 100), (0, 0, 0, 0)) # Create a blank image
        #poly = Image.new('RGBA', (100,100)) # make a mask
        #pdraw = ImageDraw.Draw(poly)
        #alpha = 0 # 0 is transparent, 255 is white
        #if abs(bias_dir) > 135:
            #alpha = alpha + 225
        #elif abs(bias_dir) > 90:
            #alpha = alpha + 175
        #elif abs(bias_dir) > 45:
            #alpha = alpha + 100
        #elif abs(bias_dir) > 20:
            #alpha = alpha + 50
        #else:
            #alpha = 0 
        #pdraw.ellipse((40,40,60,60), fill = (255,255,255,alpha)) #set last parameter in fill to adj alpha
        if bias_spd < 0: #color and size based on speed
            draw = ImageDraw.Draw(image)
            draw.ellipse((40, 40, 60, 60), fill=(0, 0, 255)) # Draw a blue circle
            if(pred_dir > obs_dir):
                if(abs(pred_dir - obs_dir) < 180):
                    pie_start = int(obs_dir)
                    pie_end = int(pred_dir)
                else:
                    pie_start = int(pred_dir)
                    pie_end = int(obs_dir)
                draw.pieslice((40,40,60,60), pie_start-90, pie_end-90, fill="white")
            elif(pred_dir < obs_dir):
                if(abs(pred_dir - obs_dir) < 180):
                    pie_start = int(pred_dir)
                    pie_end = int(obs_dir)
                else:
                    pie_start = int(obs_dir)
                    pie_end = int(pred_dir)
                draw.pieslice((40,40,60,60), pie_start-90, pie_end-90, fill="white")
           #if bias is 0 or obs is None don't draw pie slice...

        elif bias_spd >= 0: #color and size based on speed
            draw = ImageDraw.Draw(image)
            draw.ellipse((40, 40, 60, 60), fill=(255, 0, 0)) # Draw a red circle
            if(pred_dir > obs_dir):
                if(abs(pred_dir - obs_dir) < 180):
                    pie_start = int(obs_dir)
                    pie_end = int(pred_dir)
                else:
                    pie_start = int(pred_dir)
                    pie_end = int(obs_dir)
            elif(pred_dir < obs_dir):
                if(abs(pred_dir - obs_dir) < 180):
                    pie_start = int(pred_dir)
                    pie_end = int(obs_dir)
                else:
                    pie_start = int(obs_dir)
                    pie_end = int(pred_dir)
            draw.pieslice((40,40,60,60), pie_start-90, pie_end-90, fill="white")

        image.save("%s.png" % plot, "PNG")
        icon = '%s.png' % plot # set icon to be the image just created
        #print 'icon = ', icon
        kmz.write(icon)
        if(initType == 'wxModel'):
            kmz_wx.write(icon)
        os.remove(icon) 
        
        
    #elif bias_spd < 0:
        #icon = 'blue_circle.png'
    #elif bias_spd >= 0:
        #icon = 'red_circle.png'
    #else:
        #print "Can't determine which icon to use for bias" 
    scale = 1.0
    if icon == 'wx_station.png':
        scale = 1.5
    elif abs(bias_spd) > 10:
        scale = scale*6.5
    elif abs(bias_spd) > 5:
        scale = scale*4.0
    elif abs(bias_spd) > 3:
        scale = scale*3.5
    elif abs(bias_spd) > 2:
        scale = scale*3.0
    elif abs(bias_spd) > 1:
        scale = scale*2.5
    else:
        scale = 2.0

    kml =               '  <Style id="sn_hide">\n' \
                        '    <LabelStyle>\n' \
                        '      <scale>0</scale>\n' \
                        '    </LabelStyle>\n' \
                        '  </Style>\n' \
                        '  <Placemark>\n' \
                        '    <Style>\n' \
                        '      <IconStyle>\n' \
                        '        <scale>%d</scale>\n' \
                        '        <Icon>\n' \
                        '          <href>%s</href>\n' \
                        '        </Icon>\n' \
                        '      </IconStyle>\n' \
                        '    </Style>\n' \
                        '    <name>%s</name>\n' \
                        '    <styleUrl>#sn_hide</styleUrl>\n' \
                        '    <Point>\n' \
                        '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                        '    </Point>\n' \
                        '    <ExtendedData>\n' \
                        '      <Data name="Observed Speed">\n' \
                        '        <value>%.1f m/s</value>\n' \
                        '      </Data>\n' \
                        '      <Data name="Predicted Speed">\n' \
                        '        <value>%.1f m/s</value>\n' \
                        '      </Data>\n' \
                        '      <Data name="Speed Bias">\n' \
                        '        <value>%.1f m/s</value>\n' \
                        '      </Data>\n' \
                        '      <Data name="Observed Direction">\n' \
                        '        <value>%.0f</value>\n' \
                        '      </Data>\n' \
                        '      <Data name="Predicted Direction">\n' \
                        '        <value>%.0f</value>\n' \
                        '      </Data>\n' \
                        '      <Data name="Direction Bias">\n' \
                        '        <value>%.0f</value>\n' \
                        '      </Data>\n' \
                        '    </ExtendedData>\n' % (scale, icon, plot, lon, lat, obs_spd, pred_spd, 
                                                   bias_spd, obs_dir, pred_dir, bias_dir)
    kml = kml +         '    <description>\n' \
                        '      <![CDATA[\n'
    kml = kml +         '      ]]>\n' \
                        '    </description>\n' \
                        '  </Placemark>\n'
    return kml


#=====================================================================================
#                   Create icons for bias map.
#=====================================================================================

#---wx station symbol----------
image = Image.new('RGBA', (100, 100), (0, 0, 0, 0)) # Create a blank image
draw = ImageDraw.Draw(image) # Create a draw object
xy = list()
xy.append((50,20))
xy.append((50,90))
fill=(255, 255, 0)
draw.line(xy, fill, width=2)
xy = list()
xy.append((50,20))
xy.append((90,40))
xy.append((50,50))
draw.polygon(xy, fill)
image.save("wx_station.png", "PNG")

#---date/time box--------------
image = Image.new('RGBA', (400, 200), (0, 0, 0, 0)) # Create a blank image
draw = ImageDraw.Draw(image) # Create a draw object
string = fcast_start
if initType == 'wxModel':
    string += ' - ' + fcast_end
position = (20,10) # upper left corner
draw.text(position, string, fill)
image.save("date_time.png", "PNG")

#---wind direction arrow-------
repPlots = list()
repPlots = ['R2', 'R3', 'R4', 'R1', 'R5', 'R23_2', 'TSW_12', 'R33', 'R13', 'R24']
direction = list()

for plot in repPlots:
    try:
        timeStart = datetime.datetime.strptime(fcast_start, "%Y-%b-%d %H:%M:%S")
        timeEnd = datetime.datetime.strptime(fcast_end, "%Y-%b-%d %H:%M:%S")
        if timeStart == timeEnd: #if it's a single hour forecast
            timeStart -=  datetime.timedelta(minutes = 5)#average over 5 min
            timeEnd += datetime.timedelta(minutes = 5) 
        print 'timeStart = ', timeStart.strftime('%Y-%m-%d %H:%M:%S')
        print 'timeEnd = ', timeEnd.strftime('%Y-%m-%d %H:%M:%S')
        data = extract_point(timeStart, timeEnd, nominalTime='') #avg over the entire period
        if data[6] != 'BADVANE':
            obs_dir = data[4] 
        print 'Plot = ', plot
        print 'data = ', data
        if obs_dir != '':
            direction.append(obs_dir)
            print direction
    except:
        print 'Could not extract wind direction data from plot %s.' % plot
        continue

samples = numpy.array(direction)
direction_mean = stats.morestats.circmean(samples, 360, 0)

rotated_direction = direction_mean + 100
if rotated_direction > 360:
    rotated_direction = rotated_direction - 360


image = Image.new('RGBA', (100, 100), (0, 0, 0, 0)) # Create a blank image
draw = ImageDraw.Draw(image) # Create a draw object
xy = list()
xy.append((50,20))
xy.append((50,80))
fill=(255, 255, 0) #yellow
draw.line(xy, fill, width=2)
xy = list()
xy.append((50,20))
xy.append((30,40))
draw.line(xy, fill, width=2)
xy = list()
xy.append((50,20))
xy.append((70,40))
draw.line(xy, fill, width=2)
newImage = image.rotate(rotated_direction)  #rotate to average wind direction
newImage.save("arrow.png", "PNG")

#=====================================================================================
#                  Prepare output files for writing.
#=====================================================================================
#--------wn kml-----------------------------------------------------------------------
kmlfile = 'doc.kml'
fout = open(kmlfile, 'w')

fout.write('<Document>\n')
fout.write('  <Icon>\n')
fout.write('    <href>ffs_icon.ico</href>\n') 
fout.write('   </Icon>\n')
fout.write('  <visibility>0</visibility>\n')
fout.write('  <name>Bias Field</name>\n')
fout.write('  <description><![CDATA[Click on blue link above for map information.<br><br>\n')
fout.write('  <b>Forecast file:</b><br>\n')
fout.write('  %s<br><br>\n' % forecast_file)
fout.write('  <b>Forecast  time:</b><br>\n')
fout.write('  %s<br><br>\n' % fcast_start)
fout.write('  ]]></description>\n')

fout.write('<ScreenOverlay>\n')
fout.write('<name>Date-Time</name>\n')
fout.write('<visibility>1</visibility>\n')
fout.write('<Snippet maxLines="0"></Snippet>\n')
fout.write('<Icon>\n')
fout.write('<href>date_time.png</href>\n')
fout.write('</Icon>\n')
fout.write('<overlayXY x="0.5" y="1" xunits="fraction" yunits="fraction"/>\n')
fout.write('<screenXY x="0.55" y="1" xunits="fraction" yunits="fraction"/>\n')
fout.write('<rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
fout.write('<size x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>\n')
fout.write('</ScreenOverlay>\n')

fout.write('<ScreenOverlay>\n')
fout.write('<name>Prevailing Wind Direction</name>\n')
fout.write('<visibility>1</visibility>\n')
fout.write('<Snippet maxLines="0"></Snippet>\n')
fout.write('<Icon>\n')
fout.write('<href>arrow.png</href>\n')
fout.write('</Icon>\n')
fout.write('<overlayXY x="0.5" y="1" xunits="fraction" yunits="fraction"/>\n')
fout.write('<screenXY x="0.08" y="0.95" xunits="fraction" yunits="fraction"/>\n')
fout.write('<rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
fout.write('<size x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
fout.write('</ScreenOverlay>\n')

fout.write('<Folder>\n')
fout.write('  <name>Bias</name>\n')

#--------wx kml-----------------------------------------------------------------------
if(initType == 'wxModel'):
    kmlfile_wx = 'doc_wx.kml'
    fout_wx = open(kmlfile_wx, 'w')

    fout_wx.write('<Document>\n')
    fout_wx.write('  <Icon>\n')
    fout_wx.write('    <href>ffs_icon.ico</href>\n') 
    fout_wx.write('   </Icon>\n')
    fout_wx.write('  <visibility>0</visibility>\n')
    fout_wx.write('  <name>Bias Field WX</name>\n')
    fout_wx.write('  <description><![CDATA[Click on blue link above for map information.<br><br>\n')
    fout_wx.write('  <b>Forecast file:</b><br>\n')
    fout_wx.write('  %s<br><br>\n' % forecast_file)
    fout_wx.write('  <b>Forecast  time:</b><br>\n')
    fout_wx.write('  %s<br><br>\n' % fcast_start)
    fout_wx.write('  ]]></description>\n')

    fout_wx.write('<ScreenOverlay>\n')
    fout_wx.write('<name>Date-Time</name>\n')
    fout_wx.write('<visibility>1</visibility>\n')
    fout_wx.write('<Snippet maxLines="0"></Snippet>\n')
    fout_wx.write('<Icon>\n')
    fout_wx.write('<href>date_time.png</href>\n')
    fout_wx.write('</Icon>\n')
    fout_wx.write('<overlayXY x="0.5" y="1" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<screenXY x="0.55" y="1" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<size x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('</ScreenOverlay>\n')

    fout_wx.write('<ScreenOverlay>\n')
    fout_wx.write('<name>Prevailing Wind Direction</name>\n')
    fout_wx.write('<visibility>1</visibility>\n')
    fout_wx.write('<Snippet maxLines="0"></Snippet>\n')
    fout_wx.write('<Icon>\n')
    fout_wx.write('<href>arrow.png</href>\n')
    fout_wx.write('</Icon>\n')
    fout_wx.write('<overlayXY x="0.5" y="1" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<screenXY x="0.08" y="0.95" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('<size x="0" y="0" xunits="fraction" yunits="fraction"/>\n')
    fout_wx.write('</ScreenOverlay>\n')

    fout_wx.write('<Folder>\n')
    fout_wx.write('  <name>WX_Bias</name>\n')
#-------------------------------------------------------------------------------------

filename = outFile + '.kmz'
kmz = zipfile.ZipFile(filename, 'w', 0, False)

if(initType == 'wxModel'):
    filename_wx = outFile + '_wx.kmz'
    kmz_wx = zipfile.ZipFile(filename_wx, 'w', 0, False)

f = open("%s.txt" % outFile, 'w')
if(initType =='point'):
    f.write('Plot,lat,lon,datetime,obs_speed(m/s),pred_speed(m/s),bias_speed(m/s),obs_dir,pred_dir,bias_dir\n')
elif(initType == 'wxModel'):
    f.write('Plot,lat,lon,datetime,obs_speed(m/s),pred_speed(m/s),bias_speed(m/s),obs_dir,pred_dir,bias_dir,wx_speed(m/s),wx_bias_speed(m/s),wx_dir,wx_bias_dir\n')
else:
    print 'Don\'t know how to write headers, can\'t determine initializaiton method used for forecast.'

#=====================================================================================
#                  Omit the initialization plots.
#=====================================================================================
omitPlots = list()

if initialization_plots_file != None:
    if(initType == 'point'):
        fin = open(initialization_plots_file, 'r')
        line = fin.readline()
        line = line.split(",")
        for i in range(len(line)):
            if line[i] != '':
                omitPlots.append(line[i])
        fin.close()

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
        if(initType == 'point'):
            f.write('%s,%.4f,%.4f,%s,%.1f,%.1f,%.1f,%.0f,%.0f,%.0f\n' % (plot, lat, lon, date_time,
                    obs_spd, pred_spd, bias_spd, obs_dir, pred_dir, bias_dir))
        elif(initType == 'wxModel'):
            u_wx = float(line.split(",")[8])
            v_wx = float(line.split(",")[9])
            w_wx = float(line.split(",")[10])
            wx_spd = ((u_wx*u_wx+v_wx*v_wx)**0.5)
            wx_bias_spd = wx_spd - obs_spd
            wx_dir = math.atan2(-u_wx,-v_wx)*180/math.pi
            if wx_dir < 0:
                wx_dir = wx_dir + 360
            wx_bias_dir = abs(wx_dir - obs_dir)
            if wx_bias_dir > 180:
                wx_bias_dir = wx_bias_dir - 180
            f.write('%s,%.4f,%.4f,%s,%.1f,%.1f,%.1f,%.0f,%.0f,%.0f,%.1f,%.1f,%.0f,%.0f\n' % (plot, lat, lon, date_time,
                obs_spd, pred_spd, bias_spd, obs_dir, pred_dir, bias_dir, wx_spd, wx_bias_spd, wx_dir, wx_bias_dir))
        else:
            print 'Can\'t write bias data, don\'t know what type of initialization was used.'
    except:
        print 'some errors, not all points written...'
        continue   
            
fin.close()
f.close()
print '%s.txt written.' % outFile


#=====================================================================================
#                   Write the kml(s).
#=====================================================================================
plots = list()
f = open("%s.txt" % outFile, 'r') #read the output file we just wrote to summarize and write kmls
line = f.readline() #read headers
while True: #make a list of plots
    line = f.readline()
    if len(line) == 0:
        break #EOF
    if line.split(",")[0] not in plots:
        plots.append(line.split(",")[0])
f.close()

for plot in plots:
    wx_bias_spd = list()
    obs_spd = list()
    wx_spd = list()
    obs_dir = list()
    wx_dir = list()
    wx_bias_dir = list()
    bias_spd = list()
    pred_spd = list()
    pred_dir = list()
    bias_dir = list()
    f = open("%s.txt" % outFile, 'r')
    line = f.readline() #read headers
    while True:
        line = f.readline()
        if len(line) == 0:
            break #EOF
        if line.split(",")[0] == plot:
            lat = float(line.split(",")[1])
            lon = float(line.split(",")[2])
            if(initType == 'wxModel'):
                obs_spd.append(float(line.split(",")[4]))
                pred_spd.append(float(line.split(",")[5]))
                bias_spd.append(float(line.split(",")[6]))
                obs_dir.append(float(line.split(",")[7]))
                pred_dir.append(float(line.split(",")[8]))
                bias_dir.append(float(line.split(",")[9]))
                wx_spd.append(float(line.split(",")[10]))
                wx_bias_spd.append(float(line.split(",")[11]))
                wx_dir.append(float(line.split(",")[12]))
                wx_bias_dir.append(float(line.split(",")[13]))
            elif (initType == 'point'):
                obs_spd.append(float(line.split(",")[4]))
                pred_spd.append(float(line.split(",")[5]))
                bias_spd.append(float(line.split(",")[6]))
                obs_dir.append(float(line.split(",")[7]))
                pred_dir.append(float(line.split(",")[8]))
                bias_dir.append(float(line.split(",")[9]))
            else:
                print 'Can\'t determine initialization type to create kml files.'
    #calculate plot averages after reading entire file
    if(initType == 'wxModel'):
        samples = numpy.array(wx_bias_spd)
        wx_bias_spd_mean = numpy.mean(samples)
        samples = numpy.array(obs_spd)
        obs_spd_mean = numpy.mean(samples)
        samples = numpy.array(wx_spd)
        wx_spd_mean = numpy.mean(samples)
        samples = numpy.array(obs_dir)
        obs_dir_mean = stats.morestats.circmean(samples, 360, 0)
        samples = numpy.array(wx_dir)
        wx_dir_mean = stats.morestats.circmean(samples, 360, 0)
        wx_bias_dir_mean = wx_dir_mean - obs_dir_mean
        
        #write the kml for this plot
        wx_kml = create_kml(plot, lat, lon, wx_bias_spd_mean, obs_spd_mean, 
                            wx_spd_mean, obs_dir_mean, wx_dir_mean, wx_bias_dir_mean)
        fout_wx.write(wx_kml)
    
    samples = numpy.array(bias_spd)
    bias_spd_mean = numpy.mean(samples)
    samples = numpy.array(obs_spd)
    obs_spd_mean = numpy.mean(samples)
    samples = numpy.array(pred_spd)
    pred_spd_mean = numpy.mean(samples)
    samples = numpy.array(obs_dir)
    obs_dir_mean = stats.morestats.circmean(samples, 360, 0)
    samples = numpy.array(pred_dir)
    pred_dir_mean = stats.morestats.circmean(samples, 360, 0)
    bias_dir_mean = pred_dir_mean - obs_dir_mean
    
    #write the kml for this plot
    kml = create_kml(plot, lat, lon, bias_spd_mean, obs_spd_mean, pred_spd_mean, 
                     obs_dir_mean, pred_dir_mean, bias_dir_mean)
    fout.write(kml)
    f.close()

#=====================================================================================
#                   Write the kmz(s).
#=====================================================================================

fout.write('</Folder>\n')
fout.write('</Document>\n')
fout.close()

kmz.write(kmlfile)

kmz.write('wx_station.png')
kmz.write('date_time.png')
kmz.write('arrow.png')
kmz.close()
print filename, 'written.'
os.remove(kmlfile)
if(initType == 'point'):
    os.remove('wx_station.png')
    os.remove('date_time.png')
    os.remove('arrow.png')

#-------wx kmz---------------------------------------------
if(initType == 'wxModel'):
    fout_wx.write('</Folder>\n')
    fout_wx.write('</Document>\n')
    fout_wx.close()
    kmz_wx.write(kmlfile_wx)

    kmz_wx.write('wx_station.png')
    kmz_wx.write('date_time.png')
    kmz_wx.write('arrow.png')
    kmz_wx.close()
    print filename_wx, 'written.'
    os.remove('wx_station.png')
    os.remove('date_time.png')
    os.remove('arrow.png')
    os.remove(kmlfile_wx)

    
    
