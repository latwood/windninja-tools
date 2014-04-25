library(devtools)
install_github('windtools', 'nwagenbrenner')
library(windtools)

#==========observed data tests====================================

fileName <- '/home/natalie/observations_paper/bsb_obs_alldata.txt'
#fileName <- '/home/natalie/observations_paper/salmon_obs_alldata.txt'
d<-readData(fileName)

#plotSensorSpeed(d, 'R2')
#plotSensorSpeed(d, 'NM1')

dsub<-subsetOnSpeed(d, 'R2', '>', 6.0)
#dsub<-subsetOnSpeed(d, 'NM1', '<', 5.0)
davg<- buildHourlyAverages(dsub)
h <- c(0, 1, 2, 3, 4, 5)
dsubhour <- subsetOnHour(davg, h)

#order<-c(11, 16, 0)
dsubhour <- reorderFactor(dsubhour, 'hour', order)

#omit ridgetop sensors
#temp<-subset(dsubhour, subset=(!(plot %in% c('R26', 'R35', 'TSW7', 'R15'))))

#bsb
lat = 43.402726
lon = -113.027724
zoom = 13
maptype = 'terrain'

#src
lat = 45.401667
lon = -116.228889
zoom = 14
maptype = 'terrain'        

m<-makeVectorMap(dsubhour, lat, lon, zoom, maptype, colorscale='continuous', axis_labels=FALSE)

#=============================bias tests=======================================
#butte
namFile = '/home/natalie/model_evaluations/bsb/5day/NAM/output/bias.txt'
hrrrFile = '/home/natalie/model_evaluations/bsb/5day/HRRR/output/bias.txt'
wrfuwFile = '/home/natalie/model_evaluations/bsb/5day/WRF-UW/output/bias.txt'
wrfnarrFile = '/home/natalie/model_evaluations/bsb/5day/WRF-NARR/output/bias.txt'

#salmon
namFile = '/home/natalie/model_evaluations/salmon_river/5day/NAM/output/bias.txt'
hrrrFile = '/home/natalie/model_evaluations/salmon_river/5day/HRRR/output/bias.txt'
wrfuwFile = '/home/natalie/model_evaluations/salmon_river/5day/WRF-UW/output/bias.txt'
wrfnarrFile = '/home/natalie/model_evaluations/salmon_river/5day/WRF-NARR/output/bias.txt'

#butte long-term
namFile = '/home/natalie/model_evaluations/bsb/long_term/NAM/output/bias.txt'
wrfnarrFile = '/home/natalie/model_evaluations/bsb/long_term/WRF-NARR/output/bias.txt'

#salmon long-term
namFile = '/home/natalie/model_evaluations/salmon_river/long_term/NAM/output/bias.txt'
wrfnarrFile = '/home/natalie/model_evaluations/salmon_river/long_term/WRF-NARR/output/bias.txt'

bias_nam<-wnReadBiasData(namFile, 'w')
#bias_hrrr<-wnReadBiasData(hrrrFile, 'w')
#bias_wrfuw<-wnReadBiasData(wrfuwFile, 'w')
bias_wrfnarr<-wnReadBiasData(wrfnarrFile, 'w')

#l <- list(bias_nam, bias_hrrr, bias_wrfuw, bias_wrfnarr) #list of dfs to combine
#l2 <- list("NAM", "HRRR", "WRFUW", "WRFNARR") #list of forecast names

l <- list(bias_nam, bias_wrfnarr) #list of dfs to combine
l2 <- list("NAM", "WRFNARR") #list of forecast names

data<-wnBuildBiasDf(l, l2) #build main df

sensorList <- list("R26")
notSensorList <- list("R26")

#===time series plots====
timeDf <- wnBuildTsDf(data, sensorList=sensorList)

sub <- subset(data, subset=(datetime > '2010-Jun-14' & datetime < '2010-Jun-30'))
timeDf <- wnBuildTsDf(sub)
wnPlotSpeedTs(timeDf)

wnPlotDirTs(timeDf)

#===box plots====
box <- wnBoxplot(data, 'bias_speed', TRUE)

#===scatter plots===
color_list <- c("darkorange", "red", "darkgreen", "darkblue")

t <- wnPlotBiasVsObs(data, 'speed')

sub <- subset(data, subset=(datetime > '2010-Jun-14' & datetime < '2010-Jun-30' & plot != 'R26'))
t <- wnPlotObsVsPred(sub, 'speed', color_list=color_list)



test <- wnBuildTsDf(sub, sensorList=sensorList)
wnPlotSpeedTs(test)

#===subset based on hour===
# for looking specific flow events (single hours)
sub <- subset(dsub, subset=(as.POSIXlt(dsub$datetime)$hour < 5 |
                            as.POSIXlt(dsub$datetime)$hour == 23 |
                            as.POSIXlt(dsub$datetime)$hour == 22 |
                            as.POSIXlt(dsub$datetime)$hour == 21))
r1 <- subset(sub, subset=(plot == 'R1'))
sub1<- subset(dsub, subset=(datetime == '2010-07-04 21:00:00'))
davg<- buildHourlyAverages(sub1)

#bsb
lat = 43.402726
lon = -113.027724
zoom = 12
maptype = 'terrain'
m<-makeVectorMap(davg, lat, lon, zoom, maptype, colorscale='continuous', axis_labels=FALSE)




