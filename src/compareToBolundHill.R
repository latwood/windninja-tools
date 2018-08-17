library(raster)
library(ggplot2)

#r<-raster('/home/natalie/bolund_hill/elevation/Bolund.grd')
#crs(r)<-"+init=epsg:25832"

r<-raster('/home/natalie/bolund_hill/elevation/bolund_hill.tif')

#--------------------------------
#read in the observed data
#--------------------------------
datafile1<-'Dir_270.dat'
datafile3<-'Dir_239.dat'
datafile4<-'Dir_90.dat'

d1<-read.table(paste0('/home/natalie/bolund_hill/measurements/Measurements/', datafile1), header=TRUE, sep=",")
colnames(d1)<-c('ID','invL','Samples','x','y','z','gl','ustar','veldustar','udustar','vdustar','wdustar','tkedustarsq','uudustarsq','vvdustarsq','wwdustarsq','ustardustar')

d3<-read.table(paste0('/home/natalie/bolund_hill/measurements/Measurements/', datafile3), header=TRUE, sep=",")
colnames(d3)<-c('ID','invL','Samples','x','y','z','gl','ustar','veldustar','udustar','vdustar','wdustar','tkedustarsq','uudustarsq','vvdustarsq','wwdustarsq','ustardustar')

d4<-read.table(paste0('/home/natalie/bolund_hill/measurements/Measurements/', datafile4), header=TRUE, sep=",")
colnames(d4)<-c('ID','invL','Samples','x','y','z','gl','ustar','veldustar','udustar','vdustar','wdustar','tkedustarsq','uudustarsq','vvdustarsq','wwdustarsq','ustardustar')

#5-m wind speeds
base_speed1 <- 10.9 #case 1, 270 degrees
base_speed3 <- 10 #case 3, 242 degrees
base_speed4 <- 7.6 #case 4, 90 degrees

#-----2-m data along transect B (270 degrees)
#d2m<-subset(d, ID %in% c('M7Z02S','M6Z02S','M3Z02S','M8Z02S'))
#d2m$speed<-(d2m$veldustar * d2m$ustar)
#d2m$speedup<-((d2m$speed-base_speed)/base_speed)

#-----5-m data along transect B (270 degrees)
d5mB<-subset(d1, ID %in% c('M7Z05S','M6Z05S','M3Z05S','M8Z05S'))
d5mB$speed<-(d5mB$veldustar * d5mB$ustar)
d5mB$speedup<-((d5mB$speed-base_speed1)/base_speed1)

#-----5-m data along transect A (239 degrees)
d5mA<-subset(d3, ID %in% c('M0Z05S','M1Z05S','M2Z05S','M3Z05S','M4Z05S'))
d5mA$speed<-(d5mA$veldustar * d5mA$ustar)
d5mA$speedup<-((d5mA$speed-base_speed3)/base_speed3)

#--------------------------------
#read in predicted data
#--------------------------------
#s1<-raster('/home/natalie/bolund_hill/windninja/NINJAFOAM_bolund_hill_extended_4Mcells/ninjaout.asc')
s1<-raster('/home/natalie/bolund_hill/windninja/NINJAFOAM_bolund_hill_extended_finemesh_originalsettings/bolund_hill_extended_270_11_0m_vel.asc')
s3<-raster('/home/natalie/bolund_hill/windninja/case3_242/bolund_hill_extended_242_10_0m_vel.asc')
#s1<-raster('/home/natalie/bolund_hill/windninja/NINJAFOAM_bolund_hill_extended_4Mcells/ninjaout_2m.asc')

#--------------------------------
#create the transects 
#--------------------------------
#get zero point for transects 
spZero<-as.data.frame(cbind(0, 0))
colnames(spZero)<-c("lon","lat")
spZero<-SpatialPoints(spZero)
#calculate distance from each cell in domain to spZero (0,0)
dist<-distanceFromPoints(s1, spZero) 

#----------------------------------------------------------------------------------
# Transect B (270)
#----------------------------------------------------------------------------------
#create SpatialLine for Transect B (270 degrees)
x=c(xmin(s1), xmax(s1))
y=c(0, 0)
slB = SpatialLines(list(Lines(Line(cbind(x,y)), ID="b")))

#extract predicted values along the transect
predSpeedLineB<-extract(s1, slB, method='simple')[[1]]
#extract cell distances from starting point along the transect
distance<-extract(dist, slB, method='simple')[[1]] 
distance[1:1600]<--distance[1:1600]
#make df with pred speed and distance along transect
predB<-as.data.frame(cbind(distance, predSpeedLineB))

#----------------------------------------------------------------------------------
# Transect A (239)
#----------------------------------------------------------------------------------
#create SpatialLine for Transect A (239 degrees)
x=c(-200, 200)
y=c(-113.2, 115.5)
slA = SpatialLines(list(Lines(Line(cbind(x,y)), ID="a")))

#extract predicted values along the transect
predSpeedLineA<-extract(s3, slA, method='simple')[[1]]
#extract cell distances from starting point along the transect
distance<-extract(dist, slA, method='simple')[[1]] 
distance[1:1258]<--distance[1:1258]
#make df with pred speed and distance along transect
predA<-as.data.frame(cbind(distance, predSpeedLineA))
#----------------------------------------------------------------------------------

#--------------------------------
#create obs-pred df for each case
#--------------------------------
keep<-c("ID","x","y","speed","speedup")
b<-d5mB[, keep, drop=FALSE]
b$transect<-"Line B"
b$dist<-b$x

a<-d5mA[, keep, drop=FALSE]
a$transect<-"Line A"
a$dist<-a$x

#add speed-up to pred df
predB$predSpeedUpLineB<-(predB$predSpeedLineB - base_speed1)/base_speed1
predA$predSpeedUpLineA<-(predA$predSpeedLineA - base_speed3)/base_speed3

p<-ggplot(predA, aes(x=distance, y=predSpeedUpLineA)) +
    geom_line() +
    #stat_smooth( method = "lm", formula = y ~ poly(x, 27), se = FALSE) +
    xlab("Distance (m)") + ylab("Speed-up") +
    theme_bw()
p <- p + theme(axis.text = element_text(size = 14))
p <- p + theme(axis.title = element_text(size = 14))
p <- p + scale_y_continuous(limits=c(-1.5, 1.5))
p <- p + scale_x_continuous(limits=c(-150, 150))
p <- p + geom_point(data=a, mapping=aes(x=x, y=speedup))


#----------------------------------------------------
#Plot terrain with transects and observation points
#----------------------------------------------------
#add spatial points for observations
lineB<-cbind(d5mB$x, d5mB$y)
colnames(lineB)<-c('lon', 'lat')
spB<-SpatialPoints(lineB)
obsA<-cbind(d5mA$x, d5mA$y)
colnames(obsA)<-c('lon', 'lat')
spObsA<-SpatialPoints(obsA)

r<-raster('/home/natalie/bolund_hill/elevation/bolund_hill_extended.tif')
#r<-raster('/home/natalie/bolund_hill/elevation/bolund_hill.tif')
plot(r)
contour(r, add=TRUE)
plot(slA, add=TRUE)
plot(slB, add=TRUE)
plot(spObsA, add=TRUE)
plot(spB, add=TRUE)

