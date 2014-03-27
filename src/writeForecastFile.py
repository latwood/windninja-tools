#!/usr/bin/python

import os
import sys

def Usage():
    print '\n    writeForecastFile.py path ext'
    print '\n    path: full path to weather files'
    print '\n    ext: weather file extension (e.g., .grb2, .nc)'
    print '\n    A list of all files with the specifed extenstion will be written'
    print '    to a file called forecast_list.txt in the working directory.'
    print '    This file can be used by runWN.py to automate a series of weather'
    print '    model runs from multiple weather files.\n' 
    sys.exit(0)

fdir = None
ext = None

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
        if fdir is None:
            fdir = argv[i]
        elif ext is None:
            ext = argv[i] 
        else:
            Usage()

        i = i + 1

    if len(argv) < 3:
        print "\n    Not enough args..."
        Usage()


#fdir = '/media/Elements/NAM/201006'
#ext = '.grb2'

fout = open("forecast_list.txt", 'w')
lst = list()

for file in os.listdir(fdir):
    if file.endswith(ext):
        lst.append(file)
        lst.sort()
        
for f in lst:
    line = fdir + '/' + f + '\n'  
    fout.write(line)

fout.close()



