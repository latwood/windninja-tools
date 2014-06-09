library(devtools)
install_github('windtools', 'nwagenbrenner')
library(windtools)

#====read data==========================================================================
#butte
namFile = '/home/natalie/model_evaluations/bsb/5day/NAM/output/bias.txt'
hrrrFile = '/home/natalie/model_evaluations/bsb/5day/HRRR/output/bias.txt'
wrfuwFile = '/home/natalie/model_evaluations/bsb/5day/WRF-UW/output/bias.txt'
wrfnarrFile = '/home/natalie/model_evaluations/bsb/5day/WRF-NARR/output/bias.txt'

#longterm butte
#namFile = '/home/natalie/model_evaluations/bsb/long_term/NAM/output/bias.txt'

#salmon
#namFile = '/home/natalie/model_evaluations/salmon_river/5day/NAM/output/bias.txt'
#hrrrFile = '/home/natalie/model_evaluations/salmon_river/5day/HRRR/output/bias.txt'
#wrfuwFile = '/home/natalie/model_evaluations/salmon_river/5day/WRF-UW/output/bias.txt'
#wrfnarrFile = '/home/natalie/model_evaluations/salmon_river/5day/WRF-NARR/output/bias.txt'

bias_nam<-wnReadBiasData(namFile, 'w')
bias_hrrr<-wnReadBiasData(hrrrFile, 'w')
bias_wrfuw<-wnReadBiasData(wrfuwFile, 'w')
bias_wrfnarr<-wnReadBiasData(wrfnarrFile, 'w')

l <- list(bias_nam, bias_hrrr, bias_wrfuw, bias_wrfnarr) #list of dfs to combine
l2 <- list("NAM", "HRRR", "WRFUW", "WRFNARR") #list of forecast names

data<-wnBuildBiasDf(l, l2) #build main df

#====subset data========================================================================

dsub<-subsetOnSpeed(data, 'R2', '>', 6.0)
dsub<-subsetOnDirection(dsub, 'R2', 210, 230)

#dsub<-subsetOnSpeed(data, 'NM1', '<', 5.0)

#====other optional subsetting==========================================================
#test <- subset(dsub, subset=(fcastType == "Weather Model" & plot=='R3' & abs(bias_speed) < 1.0))
#dsub <- subset(dsub, subset=(datetime %in% test$datetime))

#dsub <- subset(dsub, subset=(as.POSIXlt(dsub$datetime)$hour %in% c(0,1,2,3,4,5)))
#dsub <- subset(dsub, subset=(as.POSIXlt(dsub$datetime)$hour %in% c(10,11,12,13)))

#wnPlotSpeedTs(dsub)

#subset by date
#dtmin <- as.POSIXct(strptime("2010-07-18 00:00:00", '%Y-%m-%d %H:%M:%S'))
#dtmax <- as.POSIXct(strptime("2010-07-19 00:00:00", '%Y-%m-%d %H:%M:%S'))
#dsub <- subset(dsub, subset=(datetime < dtmax & datetime > dtmin))

#====make map==========================================================================

df<-dsub

#model<-"WRF-NARR (1.33 km)"
model<-"NAM (12 km)"

var<-"speed"
stat<-"bias"
breaks<-6

test<-wnCreateBubbleMap(df, model, var, stat, breaks)






