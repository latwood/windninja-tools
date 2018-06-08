#library(devtools)
#install_github('nwagenbrenner/windtools')
library(windtools)
library(xts)
library(raster)
library(ggplot2)

r<-raster('/home/natalie/bsb/rans_evaluations/big_butte_small.tif')
plot(r)
contour(r, add=TRUE)

#--------------------------------
#read in the observed data
#--------------------------------
db<-"/home/natalie/bsb/rans_evaluations/obs_data/bsb.sqlite"
sTime<-"2010-07-15 00:00:00"
eTime<-"2010-07-20 00:00:00"
sensor<-'R2'
ee<-dbFetchHourlyAvg(db,sensor,sTime,eTime,avg_time=20,align="center") 
#plot(ee,main="R2",ylab="Hourly 10-min avg speed (m/s)")

#get sensor locations and data for evaluations
#date/times to consider
#July 17 1800
#July 18 1830
#July 19 1800
#no data for TSW6,TSW13 during this time period
sTime<-"2010-07-18 00:00:00"
eTime<-"2010-07-18 00:00:00"
sensors<-c("TSW1","TSW2","TSW4", "TSW5", "TSW7", "TSW8", "TSW9", "TSW10", "TSW11", "TSW12")
for (sensor in sensors){
      #print(paste("sensor = ", sensor))
    assign(paste0("july_18_1830_",sensor), dbFetchHourlyAvg(db,sensor,sTime,eTime,avg_time=10,align="center")) 
}
locs<-dbFetchSensorLocation(db, sensors)

# convert to single df in windtools format
dtmin <- as.POSIXct(strptime("2010-07-14 00:00:00", '%Y-%m-%d %H:%M:%S'))
dtmax <- as.POSIXct(strptime("2010-07-19 00:00:00", '%Y-%m-%d %H:%M:%S'))
d.sub <- subset(d, subset=(datetime < dtmax & datetime > dtmin))
d.sub <- subset(d.sub, subset=(plot=="R2"))

dd<-as.data.frame(cbind(locs$Plot_id,locs$Latitude,locs$Longitude,ee[1,],ee[,1], dir))

dd<-as.data.frame(cbind(sd$Plot_id, d.sub$lat, d.sub$lon, sd$Date_time, sd$Wind_speed, sd$Wind_dir))
colnames(dd)<-c("plot","lat","lon","datetime","obs_speed","obs_dir")

plotSensor(dd, 'R2', var="speed")

p<-ggplot(d.sub, aes(x=datetime, y=obs_speed)) +
    geom_point() +
    xlab("Datetime") + ylab("Speed (m/s)") +
    theme_bw()
p <- p + theme(axis.text = element_text(size = 14))
p <- p + theme(axis.title = element_text(size = 14))
#p <- p + scale_y_continuous(limits=c(0, 50))
#p <- p + scale_x_continuous(limits=c(200, 600))

#5-m wind speeds
base_speed <- 7.6 #case 4, 90 degrees

#-----5-m data along transect B (270 degrees)
d5m<-subset(d, ID %in% c('M7Z05S','M6Z05S','M3Z05S','M8Z05S'))
d5m$speed<-(d5m$veldustar * d5m$ustar)
d5m$speedup<-((d5m$speed-base_speed)/base_speed)

#--------------------------------
#read in predicted data
#--------------------------------
s<-raster('/home/natalie/bsb/rans_evaluations/windninja/big_butte_220_11_30m_vel.asc')

#--------------------------------
#create the transects 
#--------------------------------
#lineB<-cbind(d5m$x, d5m$y)
#colnames(lineB)<-c('lon', 'lat')
#spB<-SpatialPoints(lineB)

#create SpatialLine for Transect B (270 degrees)
x=c(xmin(s), xmax(s))
y=c(0, 0)
slB = SpatialLines(list(Lines(Line(cbind(x,y)), ID="b")))
#plot(r)
#plot(slB, add=TRUE)

#get starting point for Transect B
spStartLine<-as.data.frame(cbind(xmin(slB), ymin(slB)))
colnames(spStartLine)<-c("lon","lat")
spStartLine<-SpatialPoints(spStartLine)
#calculate distance from each cell to the starting point of Transect B
dist<-distanceFromPoints(s, spStartLine) 
#extract predicted values along the transect
predSpeedLineB<-extract(s, slB, method='simple')[[1]]
#extract cell distances from starting point along the transect
distance<-extract(dist, slB, method='simple')[[1]] 
distance<-distance+xmin(slB)
#make df with pred speed and distance along transect
pred<-as.data.frame(cbind(distance, predSpeedLineB))

#--------------------------------
#create obs-pred df for each case
#--------------------------------
keep<-c("ID","x","y","speed","speedup")
b<-d5m[, keep, drop=FALSE]
#b<-d2m[, keep, drop=FALSE]
b$transect<-"Line B"
b$dist<-b$x

#distObs<-c(b$x - xmin(s))
#b<-cbind(b,distObs) 

#add speed-up to pred df
pred$predSpeedUpLineB<-(pred$predSpeedLineB - base_speed)/base_speed

p<-ggplot(pred, aes(x=distance, y=predSpeedUpLineB)) +
    geom_line() +
    #stat_smooth( method = "lm", formula = y ~ poly(x, 27), se = FALSE) +
    xlab("Distance (m)") + ylab("Speed-up") +
    theme_bw()
p <- p + theme(axis.text = element_text(size = 14))
p <- p + theme(axis.title = element_text(size = 14))
p <- p + scale_y_continuous(limits=c(-1, 1))
#p <- p + scale_x_continuous(limits=c(200, 600))
p <- p + scale_x_continuous(limits=c(-150, 150))
#p <- p + geom_point(data=b, mapping=aes(x=distObs, y=speedup))
p <- p + geom_point(data=b, mapping=aes(x=x, y=speedup))

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

######### old code for multiple sensors
#sd1<-dbFetchSensor(db, sensor="R2", start_time=sTime, end_time=eTime)
#sd2<-dbFetchSensor(db, sensor="R26", start_time=sTime, end_time=eTime)
#sd1[,"Date_time"] <- as.POSIXct(strptime(sd1[,"Date_time"], '%Y-%m-%d %H:%M:%S'), tz="America/Denver")
#sd2[,"Date_time"] <- as.POSIXct(strptime(sd2[,"Date_time"], '%Y-%m-%d %H:%M:%S'), tz="America/Denver")
#ts1<-xts(sd1$Wind_speed*0.447, sd1$Date_time) #*0.447 converts mph->m/s
#ts2<-xts(sd2$Wind_speed*0.447, sd2$Date_time) #*0.447 converts mph->m/s
#ts<-na.locf(merge(ts1,ts2))
#plot.zoo(ts)

#--------------------------------
#(old)read in the observed data
#--------------------------------
#db<-"/home/natalie/bsb/rans_evaluations/obs_data/bsb.sqlite"
#sTime<-"2010-07-15 00:00:00"
#eTime<-"2010-07-20 00:00:00"
#sensor<-'R2'
#
#sd<-dbFetchSensor(db, sensor="R2", start_time=sTime, end_time=eTime)
##set the tz
#sd[,"Date_time"] <- as.POSIXct(strptime(sd[,"Date_time"], '%Y-%m-%d %H:%M:%S'), tz="America/Denver")
#
##convert to xts format
#ts<-xts(sd$Wind_speed*0.447, sd$Date_time) #*0.447 converts mph->m/s
#
##compute a rolling average
#rAvg<-rollmean(ts, 2, align="center") #10-min avg
##extract the value from rAvg every hour
#e<-endpoints(rAvg,on="hours")
#ee<-rAvg[e]
#plot(ee,main="R2",ylab="Hourly 2-min avg speed (m/s)")

