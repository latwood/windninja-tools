#!/usr/bin/env Rscript

library(ggplot2)
library(ggmap)

#----------------------------------
# Update local log files
#----------------------------------
system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/logs/stats.log /home/natalie/windninja_mobile/stats.log")

system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/logs/registrations.log /home/natalie/windninja_mobile/registrations.log")

#rm spaces from email addresses
system("sed -ie 's/ @/@/g' registrations.log")

#----------------------------------
# Track users
#----------------------------------

d<-read.table('registrations.log', skip=1, stringsAsFactors=FALSE)
dd<-subset(d, select=c(V6, V7, V8, V9))
datetime<-with(dd, paste0(V6, " ", V7, " ",  V8, " ", "2016"))
ddd<-as.data.frame(cbind(datetime,as.numeric(row.names(d))), stringsAsFactors=FALSE)
colnames(ddd)<-c("datetime","install") 
ddd[,"datetime"] <- as.POSIXct(strptime(ddd[,"datetime"], '%b %d %H:%M %Y'))

d.sub<-subset(ddd, subset=(datetime > as.POSIXct(strptime("2016-07-27 00:00:00", '%Y-%m-%d %H:%M:%S')))) 
d.sub$install<-as.numeric(d.sub$install)

p<-ggplot(d.sub, aes(x=datetime, y=install)) +
    geom_point(shape=19, size=1.5, alpha = 1) +
    geom_line() +
    xlab("") + ylab("") +
    theme_bw() +
    ggtitle("WindNinja-Mobile Installs")

#p<- p + annotate(geom="text", x=as.POSIXct(strptime("2016-07-27 22:00:00", '%Y-%m-%d %H:%M:%S')), y=100, label="Total runs: 78", color="blue")
#p<- p + annotate(geom="text", x=as.POSIXct(strptime("2016-07-27 22:00:00", '%Y-%m-%d %H:%M:%S')), y=95, label="Bug reports: 0", color="blue")
#p<- p + annotate(geom="text", x=as.POSIXct(strptime("2016-07-27 22:00:00", '%Y-%m-%d %H:%M:%S')), y=90, label="Other feedback: 3", color="blue")

#write the image to disk
png("registrations.png", width=600, height=600, res=120)
print(p)
dev.off()

#----------------------------------
# Track simulations
#----------------------------------

s<-read.table('stats.log', stringsAsFactors=FALSE)
ss<-subset(s, select=c(V2,V16,V19,V22,V25,V28,V40,V48))
colnames(ss)<-c("user","xmax","xmin","ymax","ymin","forecast","datetime","job_id") 
ss$runs<-as.numeric(row.names(ss))

ss$xmax = substr(ss$xmax,1,nchar(ss$xmax)-1)
ss$xmin = substr(ss$xmin,1,nchar(ss$xmin)-1)
ss$ymax = substr(ss$ymax,1,nchar(ss$ymax)-1)
ss$ymin = substr(ss$ymin,1,nchar(ss$ymin)-2)
ss$datetime = substr(ss$datetime,3,nchar(ss$datetime))

ss$datetime<-as.POSIXct(strptime(ss$datetime, '%Y-%m-%dT%H:%M:%S', tz="GMT"))  
ss$date<-as.POSIXct(strptime(ss$datetime, '%Y-%m-%d', tz="GMT"))    

s.sub<-subset(ss, subset=(datetime > as.POSIXct(strptime("2016-07-27 00:00:00", '%Y-%m-%d %H:%M:%S')))) 

#rm developer runs
s.sub<-subset(ss, subset=(!(user %in% c("nwagenbrenner@gmail.com",
                                      "jforthofer@gmail.com",
                                      "tweber@yourdatasmarter.com",
                                      "fspataro@yourdatasmarter.com"))))

#p<-ggplot(s.sub, aes(x=datetime, y=runs)) +
#    geom_point(shape=19, size=1.5, alpha = 1) +
#    geom_line() +
#    xlab("Time") + ylab("Simulations") +
#    theme_bw() +
#    ggtitle("WindNinja-Mobile Simulations")

p<-ggplot(s.sub, aes(date, fill=forecast)) +
    geom_bar() +
    labs(fill="") +
    xlab("Time") + ylab("Simulations") +
    theme_bw() +
    ggtitle("WindNinja-Mobile Simulations")

p<- p + theme(legend.position=c(0.9,0.9))

#p<-p + theme(axis.text.x = element_text(angle = 45, hjust = 1)) 

#write the image to disk
png("simulations.png", width=964, height=480, res=72)
print(p)
dev.off()

#-------------------------------------
#  Map geographic use  
#-------------------------------------
s.sub$ymin<-as.numeric(s.sub$ymin)
s.sub$xmin<-as.numeric(s.sub$xmin)

#map<-get_map(location = c(lon = -113.04, lat = 43.38), zoom = 3, maptype = 'terrain')
map<-get_map(location = c(lon = -97.04, lat = 42.38), zoom = 4, maptype = 'terrain')

m <- ggmap(map) + geom_point(data=s.sub, aes(x=xmin, y=ymin), alpha=0.4, colour = "red", size = 1) +
        xlab("") + ylab("") 

#subset runs done within some recent times
currentTime<-Sys.time()
attr(currentTime, "tzone") <- "UTC"

s.sub.lastDay<-subset(s.sub, subset=(difftime(currentTime, s.sub$date, units="hours") < 24))
hoursSince<-24
s.sub.lastDay<-cbind(s.sub.lastDay,hoursSince)
s.sub.lastTwoDays<-subset(s.sub, subset=(difftime(currentTime, s.sub$date, units="hours") < 48 &
                                         !(s.sub$date %in% s.sub.lastDay$date)))
hoursSince<-48
s.sub.lastTwoDays<-cbind(s.sub.lastTwoDays,hoursSince)
s.sub.lastWeek<-subset(s.sub, subset=(difftime(currentTime, s.sub$date, units="hours") < 168 &
                                      !(s.sub$date %in% s.sub.lastTwoDays$date)))
hoursSince<-168
s.sub.lastWeek<-cbind(s.sub.lastWeek,hoursSince)

s.sub.recent<-rbind(s.sub.lastDay,s.sub.lastTwoDays,s.sub.lastWeek)

m.recent <- ggmap(map) + 
            geom_point(data=s.sub.recent, aes(x=xmin, y=ymin, color=as.factor(hoursSince)),
            alpha=0.5, size = 2) + xlab("") + ylab("") +
            scale_color_manual(values=c("blue", "purple", "red"),labels=c("< 1 week", "< 2 days", "< 24 hrs")) 

m.recent <- m.recent + theme(legend.position=c(0.8,0.9)) + labs(color="Time Since Run")

#write the image to disk
png("usage_map.png", width=600, height=600, res=120)
print(m)
dev.off()

png("usage_map_recent.png", width=600, height=600, res=120)
print(m.recent)
dev.off()

#-------------------------------------
#  scp images to aws
#-------------------------------------

system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" /home/natalie/windninja_mobile/simulations.png ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/ninjaonline/ninjaoutput/mobile")

system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" /home/natalie/windninja_mobile/registrations.png ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/ninjaonline/ninjaoutput/mobile")

system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" /home/natalie/windninja_mobile/usage_map.png ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/ninjaonline/ninjaoutput/mobile")

system("scp -i \"/home/natalie/.ssh/WindNinjaMobile.pem\" /home/natalie/windninja_mobile/usage_map_recent.png ubuntu@ec2-52-222-19-7.us-gov-west-1.compute.amazonaws.com:/home/ubuntu/ninjaonline/ninjaoutput/mobile")



