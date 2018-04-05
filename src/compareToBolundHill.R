library(raster)
library(ggplot2)

#r<-raster('/home/natalie/bolund_hill/elevation/Bolund.grd')
#crs(r)<-"+init=epsg:25832"

r<-raster('/home/natalie/bolund_hill/elevation/bolund_hill.tif')
plot(r)
contour(r, add=TRUE)

#--------------------------------
#read in the observed data
#--------------------------------
d<-read.table('/home/natalie/bolund_hill/measurements/Measurements/Dir_270.dat', header=TRUE, sep=",")
colnames(d)<-c('ID','invL','Samples','x','y','z','gl','ustar','veldustar','udustar','vdustar','wdustar','tkedustarsq','uudustarsq','vvdustarsq','wwdustarsq','ustardustar')

base_speed <- 10.9

#-----2-m data along transect B (270 degrees)
d2m<-subset(d, ID %in% c('M7Z02S','M6Z02S','M3Z02S','M8Z02S'))
d2m$speed<-(d_b_2m$veldustar * d_b_2m$ustar)

#-----5-m data along transect B (270 degrees)
d5m<-subset(d, ID %in% c('M7Z05S','M6Z05S','M3Z05S','M8Z05S'))
d5m$speed<-(d5m$veldustar * d5m$ustar)
d5m$speedup<-((d5m$speed-base_speed)/base_speed)

#lineB<-cbind(d5m$x, d5m$y)
#colnames(lineB)<-c('lon', 'lat')
#spB<-SpatialPoints(lineB)

#--------------------------------
#create the transects 
#--------------------------------
#create SpatialLine for Transect B (270 degrees)
x=c(-98.125, 192.375) #nrow, ncol from raster
y=c(0, 0)
slB = SpatialLines(list(Lines(Line(cbind(x,y)), ID="b")))
#plot(r)
#plot(slB, add=TRUE)

#--------------------------------
#read in predicted data
#--------------------------------
s<-raster('/home/natalie/bolund_hill/windninja/bolund_refined/NINJAFOAM_bolund_hill_myKE/bolund_hill_270_11_0m_vel.asc')

#get starting point for Transect B
spStartLine<-as.data.frame(cbind(xmin(slB), ymin(slB)))
colnames(spStartLine)<-c("lon","lat")
spStartLine<-SpatialPoints(spStartLine)
#calculate distance from each cell to the starting point of Transect B
dist<-distanceFromPoints(s, spStartLine) 
#extract predicted values along the transect
predSpeedLineB<-extract(s, slB, method='simple', cellnumbers=TRUE)[[1]]
#extract cell distances from starting point along the transect
distance<-extract(dist, slB, method='simple')[[1]] 
#make df with pred speed and distance along transect
pred<-as.data.frame(cbind(distance, predSpeedLineB))

#--------------------------------
#create obs-pred df for each case
#--------------------------------
keep<-c("ID","x","y","speed","speedup")
b<-d5m[, keep, drop=FALSE]
b$transect<-"Line B"
b$dist<-b$x
b$pred_speed<-predSpeedLineB
b$pred_speedup<-(predSpeedLineB-base_speed)/base_speed

#--------------------------------
#make some plots
#--------------------------------
pb<-plotTransect(b)
pb<-plotSpeedupTransect(b)

#--------------------------------
#functions
#--------------------------------
#plot speedup for a transect
plotSpeedupTransect<-function(df){ 
    p<-ggplot(df, aes(x=dist, y=speedup)) +
        geom_point(shape=19, size=1.5, alpha = 1) +
        xlab("Distance (m)") + ylab("Speed-up") +
        theme_bw()

    p <- p + geom_line(aes(x=dist, y=pred_speedup))
    p <- p + theme(axis.text = element_text(size = 14))
    p <- p + theme(axis.title = element_text(size = 14))
    p <- p + facet_grid(. ~ transect)
    p <- p + scale_y_continuous(limits=c(-1, 1))

    return(p)
}

#plot obs vs pred
plotTransect<-function(df){ 
    p<-ggplot(df, aes(x=dist, y=speed)) +
        geom_point(shape=19, size=1.5, alpha = 1) +
        xlab("Distance (m)") + ylab("Speed (m/s)") +
        theme_bw()

    p <- p + geom_line(aes(x=dist, y=pred_speed))
    p <- p + theme(axis.text = element_text(size = 14))
    p <- p + theme(axis.title = element_text(size = 14))
    p <- p + facet_grid(. ~ transect)
    p <- p + scale_y_continuous(limits=c(0, 20))
    p <- p + scale_x_continuous(limits=c(-100, 200))

    return(p)
}
