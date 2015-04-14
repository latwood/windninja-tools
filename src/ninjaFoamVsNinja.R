library(raster)
library(ggplot2)

r<-raster('/mnt/output/ninjafoam/askervein.tif')
plot(r)
contour(r, add=TRUE)

#Line A coords
lineA<-read.table('/mnt/output/ninjafoam/observed_data/line_a.csv', header=TRUE, sep=",")
lineAA<-read.table('/mnt/output/ninjafoam/observed_data/line_aa.csv', header=TRUE, sep=",")
lineB<-read.table('/mnt/output/ninjafoam/observed_data/line_b.csv', header=TRUE, sep=",")

colnames(lineA)<-c('lon', 'lat', 'z')
colnames(lineAA)<-c('lon', 'lat', 'z')
colnames(lineB)<-c('lon', 'lat', 'z')

lineA<-lineA[-11:-12,1:2]
lineB<-lineB[-18:-20,1:2]
lineAA<-lineAA[,1:2]

spA<-SpatialPoints(lineA)
spAA<-SpatialPoints(lineAA)
spB<-SpatialPoints(lineB)

#plot DEM with contours and sensor points
contour(r)
points(lineB, pch=20)
points(lineA, pch=20)
points(lineAA, pch=20)
plot(r, add=TRUE)

#observed data
obsLineB<-read.table("observed_data/line_b_observed.csv", header=TRUE, sep=",")
obsLineA<-read.table("observed_data/line_a_observed.csv", header=TRUE, sep=",")
obsLineAA<-read.table("observed_data/line_aa_observed.csv", header=TRUE, sep=",")

#interpolate wind predictions to sensor locations
#r<-raster('NINJAFOAM_level33_angle10_withBLcells/askervein_210_9_23m_vel.asc') #applyInit height = 2000
r<-raster('NINJAFOAM_level33_angle10_applyInit0/askervein_210_9_23m_vel.asc') #applyInit height = 0
#r<-raster('NINJAFOAM_level00_angle10/askervein_210_9_23m_vel.asc')
#r<-raster('NINJAFOAM_level11_angle10/askervein_210_9_23m_vel.asc')
nfLineAValues<-extract(r, lineA, method='bilinear')
nfLineAAValues<-extract(r, lineAA, method='bilinear')
nfLineBValues<-extract(r, lineB, method='bilinear')

#read in distances along transects
b_dist<-read.table('observed_data/dist_line_b.csv', header=TRUE, sep=",")
a_dist<-read.table('observed_data/dist_line_a.csv', header=TRUE, sep=",")
aa_dist<-read.table('observed_data/dist_line_aa.csv', header=TRUE, sep=",")

#combine observed and predicted winds
transect<-"Line B"
b<-cbind(obsLineB, nfLineBValues, b_dist, transect)
colnames(b)<-c("observed", "nfPredicted", "d", "transect")
transect<-"Line A"
a<-cbind(obsLineA, nfLineAValues, a_dist, transect)
colnames(a)<-c("observed", "nfPredicted", "d", "transect")
transect<-"Line AA"
aa<-cbind(obsLineAA, nfLineAAValues, aa_dist, transect)
colnames(aa)<-c("observed", "nfPredicted", "d", "transect")

#data<-rbind(a, aa, b)

#omit locations with obs = 0
a<-subset(a, subset=(observed!=0.0))
aa<-subset(aa, subset=(observed!=0.0))
b<-subset(b, subset=(observed!=0.0))
#data<-subset(data, subset=(observed!=0.0))

pa<-plotTransect(a)
paa<-plotTransect(aa)
pb<-plotTransect(b)

#plot obs vs pred
plotTransect<-function(df){ 
    p<-ggplot(df, aes(x=d, y=observed)) +
        geom_point(shape=19, size=1.5, alpha = 1) +
        xlab("Distance (m)") + ylab("Speed (m/s)") +
        theme_bw()

    p <- p + geom_line(aes(x=d, y=nfPredicted))
    p <- p + theme(axis.text = element_text(size = 14))
    p <- p + theme(axis.title = element_text(size = 14))
    p <- p + facet_grid(. ~ transect)
    p <- p + scale_y_continuous(limits=c(0, 20))

    return(p)
}

#=========================
# vector plots
#=========================
library(grid)
library(ggplot2)

r.dir<-raster('/mnt/output/ninjafoam/NINJAFOAM_bsb_SHM_level01/big_butte_215_10_30m_ang.asc')
r.spd<-raster('/mnt/output/ninjafoam/NINJAFOAM_bsb_SHM_level01/big_butte_215_10_30m_vel.asc')

r.dir<-raster('/mnt/output/ninjafoam/big_butte_215_10_200m_ang.asc')
r.spd<-raster('/mnt/output/ninjafoam/big_butte_215_10_200m_vel.asc')

#r.dir<-raster('/mnt/output/ninjafoam/nativesolver_bsb/big_butte_215_10_200m_ang.asc')
#r.spd<-raster('/mnt/output/ninjafoam/nativesolver_bsb/big_butte_215_10_200m_vel.asc')

r.brick<-brick(r.spd, r.dir)

#coarsen if necessary for plotting
#r.brick<-aggregate(r.brick, fact=6, fun=mean)

sp<-rasterToPoints(r.brick, spatial=TRUE)
colnames(sp@data) <- c('spd', 'dir')

crs<-CRS("+proj=longlat +datum=WGS84")
sp<-spTransform(sp, crs)

#convert to regular dataframe
d<-sp@data
d<-cbind(sp@coords, d)
colnames(d)<-c('lon', 'lat', 'spd', 'dir')

#df<-subset(df, subset=(spd < 30))

lat = 43.402726
lon = -113.027724
zoom = 13
maptype = 'terrain'

m<-rasterToVectorMap(d, lat, lon, zoom, maptype, colorscale='discrete', axis_labels=FALSE)







