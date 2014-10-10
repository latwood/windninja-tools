library(raster)
library(fields)

w<-read.table('/home/natalie/src/windninja/build/src/cli/NINJAFOAM_3759245312_0/postProcessing/surfaces/1000/U_triSurfaceSampling.raw')
colnames(w)<-c('x','y','z','ux','uy','uz')

#convert to spatialPointsDataFrame
coordinates(w) = c("x", "y")
#add projection
proj4string(w)<-CRS("+proj=utm +zone=12 +datum=WGS84 +units=m +no_defs +ellps=WGS84 +towgs84=0,0,0")

crs<-CRS("+proj=latlon +datum=WGS84ls")
w<-spTransform(w, crs)

#generate a raster to interpolate spatial points onto
r <- raster(xmn=bbox(w)[1], xmx=bbox(w)[3], ymn=bbox(w)[2], ymx=bbox(w)[4])
projection(r) <- projection(w)
res(r) <- 30

rr<-rasterize(w, r, field="ux", fun=mean)


