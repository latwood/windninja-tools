#!/usr/bin/python3

import sys
import os
import zipfile

def Usage():
    print ('image2goverlay.py wkt_prj_file src_file dst_file image_file')
    print ('Note: image_file must be in WGS84 coords (EPSG 4326); no coordinate transformation will be performed')
    sys.exit(1)

try:
    from osgeo import gdal, osr
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    try:
        import gdal
    except ImportError:
        print ('GDAL Python bindings are required')
        Usage()

srcFile = None
dstFile = None
prj_file = None
image = None

# =============================================================================
#             Parse command line options.
# =============================================================================

if __name__ == '__main__':
    argv = gdal.GeneralCmdLineProcessor( sys.argv )
    if argv is None:
        sys.exit(0)

    i = 1

    while i < len(argv):
        arg = argv[i]

        if prj_file is None:
            prj_file = argv[i]
        elif srcFile is None:
            srcFile = argv[i]
        elif dstFile is None:
            dstFile = argv[i]
        elif image is None:
            image = argv[i]
        else:
            Usage()

        i = i + 1

    if len(argv) < 5:
        print ("Not enough args...")
        Usage()

    kml_file = 'doc.kml'
    kmz_file = dstFile

# =============================================================================
#       Open ds and set gt and srs
# =============================================================================

    gdal.AllRegister()

    src_ds = gdal.Open( srcFile, GA_ReadOnly )
    driver = src_ds.GetDriver()

    fin = open( prj_file, 'r' )
    wkt_input = fin.read()
    src_sr = osr.SpatialReference()
    src_sr.ImportFromWkt( wkt_input )
    src_wkt = src_sr.ExportToWkt()
    fin.close()

    if src_wkt == '':
        print ('Cannot find spatial reference in input file')
        Usage()

    #set target osr
    dst_sr = osr.SpatialReference()
    dst_sr.ImportFromEPSG( 4326 )
    dst_wkt = dst_sr.ExportToWkt()

    #create a vrt dataset
    creation_options = []
    vrt_ds = gdal.AutoCreateWarpedVRT( src_ds, src_wkt, dst_wkt )

    #get extents
    gt = vrt_ds.GetGeoTransform()

    bounds = []

    north = gt[3] + gt[4] * 0 + gt[5] * 0
    west = gt[0] + gt[1] * 0 + gt[2] * 0
    south = gt[3] + gt[4] * 0 + gt[5] * vrt_ds.RasterYSize
    east = gt[0] + gt[1] * vrt_ds.RasterXSize + gt[2] * 0

    #write the kml file
    xml ='''<kml>
    <GroundOverlay>
    <name>%s</name>
    <Icon>
      <href>%s</href>
    </Icon>
    <LatLonBox>
      <north>%s</north>
      <south>%s</south>
      <east>%s</east>
      <west>%s</west>
    </LatLonBox>
  </GroundOverlay>
</kml>''' % ( image, image, north, south, east, west )
    

    kmlFile = open( kml_file, 'w' )
    kmlFile.write( xml )
    kmlFile.close()

# =============================================================================
#             Create and write kmz file using ZipFile
# =============================================================================

    kmz = zipfile.ZipFile( kmz_file, 'w', 0, False )

    kmz.write( kml_file )
    kmz.write( image )
    kmz.close()

    #remove files
    #driver.Delete( warped_file )
    #if os.path.exists( warped_file + '.aux.xml' ): 
        #driver.Delete( warped_file + '.aux.xml' )
    os.remove( kml_file ) 
