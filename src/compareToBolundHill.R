library(raster)
library(ggplot2)

#r<-raster('/home/natalie/bolund_hill/elevation/Bolund.grd')
#crs(r)<-"+init=epsg:25832"

r<-raster('/home/natalie/bolund_hill/elevation/bolund_hill.tif')

plot(r)
contour(r, add=TRUE)




