#!/usr/bin/python

import copy

import subprocess
import os
import sys

import datetime

def Usage():
    print '\n    runWN.py stability_flag [-f forecast_list] [start_time] [end_time]'
    print '\n    stability_flag: (T, F)'
    print '\n    start_time, end_time (for point-initialized run): start/end hour for simulation.'
    print '                          2010-07-17T00:00:00 2010-07-18T00:00:00 for one day'
    print '\n    forecast_list (for a wx model run):'
    print '                   A txt file with one .nc file listed per line.'
    print '\n    If a forecast_list is supplied, don\'t need to specify start and end times.'
    print '    If it is a point initialized run, this script will connect to the database' 
    print '    to fetch observed data and write a wxstation.csv file. Runs WindNinja in' 
    print '    current directory for each hour.\n' 
    sys.exit(0)

#=============================================================================
#             Set some initial values.
#=============================================================================

start_time = None
end_time = None
forecast_file = None
forecast_list = None
stabilityFlag = None
initMethod = 'pointInitialization'
geFlag = 'false'
asciiFlag = 'false'
#pointsFile = '/home/natalie/bsb_locations.txt'
pointsFile = '/home/natalie/salmon_locations.txt'


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
            forecast_list = argv[i]
        elif stabilityFlag is None:
            stabilityFlag = argv[i] 
        elif start_time is None:
            start_time = argv[i] 
        elif end_time is None:
	        end_time = argv[i]
        else:
            Usage()

        i = i + 1

    if len(argv) < 3:
        print "\n    Not enough args..."
        Usage()

if forecast_list == None:
    start = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
    end = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
if(forecast_list != None):
    initMethod = 'wxModelInitialization'
if(stabilityFlag == 'True' or stabilityFlag == 'T' or stabilityFlag == 'true'):
    stabilityFlag = 'true'
else:
    stabilityFlag = 'false'


##=============================================================================
#        Open a log file
#=============================================================================
startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
log = open("runWN.log", 'w')
log.write('startTime   =   %s\n' % startTime)
    
    
#=============================================================================
#   Setup directories
#=============================================================================
if os.path.isdir('output') == False:
    os.mkdir('output')
    print 'Made directory output. '

if(geFlag == 'true'):
    if os.path.isdir('output/kmz') == False:
        os.mkdir('output/kmz')

if(asciiFlag == 'true'):
    if os.path.isdir('output/ascii') == False:
        os.mkdir('output/ascii')


#=============================================================================
#      Parse forecast list input file.
#=============================================================================
if forecast_list != None:
    wxFiles = list()
    fin = open("%s" % forecast_list, 'r')
    while True:
        line = fin.readline()
        if len(line) == 0:
            log.write('Reached end of forecast_list.txt. %d lines read.\n' % len(wxFiles)) 
            break #EOF
        wxFiles.append(line)
    fin.close()

#=============================================================================
#   Write wxstation file if it's a point initialization
#=============================================================================

def writeWxStation(this_hour):
    print 'Writing wx station file...'
    fout = open("write_wxstation_input.txt", 'w')
    fout.write('plot = R18,R5,R2,R26\n') #TEST WITH R26 PLOT
    #fout.write('plot = TSW1,TWSW1,R2,R3,R4,R5,R1,R18,R23_2,R23\n') #some sensors in the flat
    # these are averaged at the top of the hour in bias_map.py
    # just need to make start_time the top of the hour and end_time also within the same hour
    fout.write('start_time = %s\n' % (this_hour.strftime('%Y-%m-%dT%H:%M:%S')))
    fout.write('end_time = %s\n' % ((this_hour + datetime.timedelta(minutes = 15)).strftime('%Y-%m-%dT%H:%M:%S')))
    fout.write('ignore_crappy = True')
    fout.close()
    wxstation = subprocess.Popen(["/home/natalie/DN/python_scripts/./writeWxStationFile.py write_wxstation_input.txt wxstation.csv"], shell = True, stdout=subprocess.PIPE)
    out, err = wxstation.communicate()
    #print 'writeWxStationFile output = ', out
    #print 'writeWxStationFile error = ', err 

#=============================================================================
#   Read in sonic.txt and set alpha for each hour
#=============================================================================
def setAlpha(this_hour):
    print 'Reading sonic.txt...'
    fin = open("sonic.txt", 'r')
    line = fin.readline() #read headers
    while True:
        line = fin.readline()
        if len(line) == 0:
            break #EOF
        if line[0] != '':
            alpha_time = datetime.datetime.strptime(line.split(",")[0], '%Y-%b-%d %H:%M:%S')
            #print 'alpha_time = ', alpha_time
            if alpha_time == this_hour:
                alpha = float(line.split(",")[8])
                break
    print 'alpha = ', alpha
    print 'alpha_time = ', alpha_time 
    log.write('alpha for current run is %.2f' % alpha)
    fin.close()
    return alpha

#=============================================================================
#   Write the cfg file
#=============================================================================
def writeWNcfg(alpha):
    fout = open("windninja.cfg", 'w')
    fout.write('num_threads                 =   1\n') #output not written in order for wx files if >1
    #fout.write('elevation_file              =   bb_fine.tif\n')
    #fout.write('elevation_file              =   big_butte.asc\n')
    fout.write('elevation_file              =   salmonriver_dem.asc\n')
    fout.write('initialization_method       =   %s\n' % initMethod)
    fout.write('time_zone                   =   America/Denver\n')
    fout.write('output_wind_height          =   3.048\n')
    fout.write('units_output_wind_height    =   m\n')
    #fout.write('vegetation                  =   brush\n')
    fout.write('vegetation                  =   grass\n')
    fout.write('mesh_choice                 =   fine\n')
    fout.write('write_goog_output           =   %s\n' % geFlag)
    fout.write('write_ascii_output          =   %s\n' % asciiFlag)
    fout.write('input_points_file           =   %s\n' % pointsFile)
    fout.write('output_points_file          =   output.txt\n')
    fout.write('diurnal_winds               =   true\n')
    fout.write('non_neutral_stability       =   %s\n' % stabilityFlag)
    if(initMethod == 'pointInitialization'):
        fout.write('wx_station_filename         =   wxstation.csv\n')
        fout.write('match_points                =   false\n')
        fout.write('alpha_stability             =   %.2f\n' % alpha)
    elif(initMethod == 'wxModelInitialization'):
        fout.write('forecast_filename       =   %s\n' % wxFile)

    fout.close()

#=============================================================================
#   Run windninja
#=============================================================================
def runWN():
    print 'Running WindNinja...'
    wn = subprocess.Popen(["/home/natalie/windninja/build/src/cli/./WindNinja_cli windninja.cfg"], shell = True, stdout=subprocess.PIPE)
    out, err = wn.communicate()
    print out
    log.write('\nWN output = ' + out + '\n')
    
#=============================================================================
#   Move output files and cleanup
#=============================================================================
def cleanup(this_hour):
    print 'Cleaning up...'
    if(initMethod == 'pointInitialization'):
        time = (this_hour).strftime('%Y%m%dT%H%M%S') # actual run time
        move_output = 'mv output.txt output_%s.txt && mv output_%s.txt output/' % (time, time)
    elif(initMethod == 'wxModelInitialization'):
        time = this_hour # the wx file name
        #time = time[(time.find('/') + 1):-4]
        time = time[(time.find('/') + 1):-1] #use for HRRR -- files don't have an extension!
        move_output = 'mv output.txt output_%s.txt && mv output_%s.txt output/' % (time, time)
    clean = subprocess.Popen([move_output], shell = True, stdout=subprocess.PIPE)
    out, err = clean.communicate()
    log.write('cleanup output = ' + out)
    if(geFlag == 'true'):
        if(initMethod == 'pointInitialization'):
            move_output = 'mv *.kmz %s.kmz && mv %s.kmz output/kmz && rm -f *.kmz' % (time, time)
        elif(initMethod == 'wxModelInitialization'):
            move_output = 'mv *.kmz output/kmz'
        clean = subprocess.Popen([move_output], shell = True, stdout=subprocess.PIPE)
        out, err = clean.communicate()
    if(asciiFlag == 'true'):
        if(initMethod == 'pointInitialization'):
            move_output = 'mv *ang.asc %s_ang.asc && mv *vel.asc %s_vel.asc &&' \
                          'mv %s_ang.asc %s_vel.asc output/ascii &&' \
                          'mv *ang.prj %s_ang.prj && mv *vel.prj %s_vel.prj &&' \
                          'rm -f *cld.asc *cld.prj *ang.asc *ang.prj *vel.asc *vel.prj' % (time, time, time, time, time, time)
        elif(initMethod == 'wxModelInitialization'):
            move_output = 'mv *ang.asc *vel.asc output/ascii'
        clean = subprocess.Popen([move_output], shell = True, stdout=subprocess.PIPE)
        out, err = clean.communicate()
    
#=============================================================================
#   Loop over hours or forecast files.
#=============================================================================    
if(initMethod == 'pointInitialization'):
    hours = int(((end - start).total_seconds())/60/60) #total hours requested
    for hour in xrange(hours):
        this_hour = start + hour * datetime.timedelta(minutes = 60)
        print 'Current time step is %s.' % this_hour.strftime('%Y-%m-%d %H:%M:%S')
        writeWxStation(this_hour)
        if stabilityFlag == 'True':
            alpha = setAlpha(this_hour)
        else:
            alpha = 1.0
        writeWNcfg(alpha)
        runWN()
        cleanup(this_hour)
        log.write('%s simulation done...\n' % (this_hour).strftime('%Y%m%dT%H%M%S'))
        if(geFlag == 'true'):
            log.write('kmz written...\n')
        if(asciiFlag == 'true'):
            log.write('ascii files written...\n')
elif(initMethod == 'wxModelInitialization'):
    for wxFile in wxFiles:
        #this_hour = wxFile # just used in cleanup to ID run
        this_hour = wxFile[wxFile.rfind("/"):] # just used in cleanup to ID run
        print 'The current wx file is %s.\n' % wxFile
        alpha = 1.0
        writeWNcfg(alpha)
        runWN()
        cleanup(this_hour) 
        log.write('%s simulation done...\n' % wxFile)
        if(geFlag == 'true'):
            log.write('kmz written...\n')
        if(asciiFlag == 'true'):
            log.write('ascii files written...\n')
else:
    print 'Can\'t determine WindNinja initialization method...'
    sys.exit(0)

#=============================================================================
#   Merge output files to a single file.
#============================================================================= 
os.chdir('output')
fileList = list()

for root, dirs, files in os.walk(os.getcwd()):
    fList = files
fList.sort()

fileList = copy.copy(fList)
    
#make combined_output.txt with just a header
fin = open(fileList[0], 'r')
fout = open('combined_output.txt', 'w')
line = fin.readline()
if(initMethod == 'pointInitialization'):
    pos = line.find(',', line.find('height'))
    line = line[0:pos+1] + 'datetime' + line[pos:]
fout.write(line)
fin.close()

if(initMethod == 'pointInitialization'): 
    for outFile in fileList:
        print 'outFile = ', outFile
        fin = open(outFile, 'r')
        line = fin.readline() #skip header
        ftemp = open("temp.txt", 'w')
        theTime = datetime.datetime.strptime(outFile[7:-4], '%Y%m%dT%H%M%S')
        while True:
            line = fin.readline()
            if len(line) == 0:
                break #EOF
            pos = line.find(',', line.find(',', line.find(',', line.find(',')+1)+1)+1)+1 #find 4th comma
            line = line[0:pos] + theTime.strftime('%Y-%b-%d %H:%M:%S') + ' MDT,' + line[pos:] #add datetime column
            fout.write(line) #append line to combined file
        ftemp.close()
        fin.close()
        os.remove("temp.txt")
    fout.close() #close combined file

elif(initMethod == 'wxModelInitialization'):
    for outFile in fileList:
        print 'outFile = ', outFile
        fin = open(outFile, 'r')
        line = fin.readline() #skip header
        ftemp = open("temp.txt", 'w')
        while True:
            line = fin.readline()
            if len(line) == 0:
                break #EOF
            fout.write(line) #append line to combined file
        ftemp.close()
        fin.close()
        os.remove("temp.txt")
    fout.close() #close combined file

log.write('Output files merged to combined_output.txt.')

#=============================================================================
#   close the log file
#=============================================================================
time = subprocess.Popen(["date"], shell = True, stdout=subprocess.PIPE)
endTime, err = time.communicate()
log.write('\nendTime     =   %s\n' % endTime)
log.close()    
    


