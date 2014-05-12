#!/usr/bin/Rscript --slave

argv <- commandArgs(TRUE)

dsn <- argv[1] #path to shpaefiles
rasters_path <- argv[2]  #path to rasters to be warped

library(maptools)
library(rgdal)
library(raster)
#library(plotGoogleMaps) #optional
#library(plotKML) #optional


#use rgdal to get CRS
#dsn <- "/home/natalie/DN/long_draw/airpact/airpact4"
ogrListLayers(dsn)
ogrInfo(dsn=dsn, layer="airpact4_sa")
#airpact4 <- readOGR(dsn=dsn, layer="airpact4_sa")

#read shapefile in and assign CRS
shp<-readShapeSpatial(paste0(dsn,'airpact4_sa'))
proj4string(shp) <- OGRSpatialRef(dsn=dsn, layer="airpact4_sa")

#get resolution and extent
cell_size<-coordinates(shp)[2] - coordinates(shp)[1]
xmin<-min(coordinates(shp)[,1])-0.5*cell_size
xmax<-max(coordinates(shp)[,1])+0.5*cell_size
ymin<-min(coordinates(shp)[,2])-0.5*cell_size
ymax<-max(coordinates(shp)[,2])+0.5*cell_size

rasters<-dir(rasters_path, pattern='*.asc')

for(i in 1:length(rasters)){
    #read in PM10 raster
    #r<-raster(paste0('/media/Elements/long_draw/test/warp/longdraw_08-06-2012_0', i, '00_597m_dust.asc'))
    r<-raster(paste0(rasters_path,rasters[i]))
    newproj<-proj4string(shp)

    #set up raster pr with correct crs and geotransform but without data
    pr <- projectExtent(r, newproj)
    extent(pr) <- extent(xmin,xmax,ymin,ymax)
    res(pr) <- cell_size

    # now project r to pr
    pr <- projectRaster(r, pr)

    #==========================================
    # convert to csv
    #==========================================
    pts<-rasterToPoints(pr, fun=NULL, spatial=FALSE)
    writeRaster(pr, filename=paste0(substr(rasters[i], 0, nchar(rasters[i])-4), '_warped.asc'), format='ascii')
    fileConn<-file(paste0(substr(rasters[i], 0, nchar(rasters[i])-4), '_warped.prj'))
    writeLines(proj4string(pr), fileConn)
    close(fileConn)
}

#===========================================
#  plot in google maps and google earth
#===========================================
#names(pr) <- "pm10"
#dust_sp<-rasterToPoints(pr, spatial=TRUE)
#dust_sp<-as(pr, 'SpatialPixelsDataFrame')
#gives error: 'Grid warping not avaialable, coercing to points' ??
#pal<-colorRampPalette(c("blue","lightblue","white","yellow", "orange", "red"))
#m<-plotGoogleMaps(dust_sp, zcol='pm10', colPalette=pal(7), mapTypeId='HYBRID',strokeWeight=1)

#plotKML(dust_sp)


#============================================
# TESTING with WindNinja shapefiles
#============================================
#shp<-readShapeSpatial('/home/natalie/windninja_trunk/build/src/cli/shapefiles/big_butte_220_10_138m')
#proj4string(shp) <- OGRSpatialRef(dsn=dsn, layer="big_butte_220_10_138m")

#ogrDrivers()
#dsn <- "/home/natalie/windninja_trunk/build/src/cli/shapefiles"
#ogrListLayers(dsn)
#ogrInfo(dsn=dsn, layer="big_butte_220_10_138m")
#wind <- readOGR(dsn=dsn, layer="big_butte_220_10_138m")
#OGRSpatialRef(dsn=dsn, layer="big_butte_220_10_138m")




