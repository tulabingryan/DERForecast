import sys
import os
import time
import datetime
import csv
import numpy as np
import math
import glob
import random
from .solar import *



def get_windPower(installedWind, windspeed, temperature):
	# This function predicts the output power of wind power given the windspeed
	windspeed = float(windspeed)
	temperature = float(temperature)
	installedWind = float(installedWind)

	rho = (0.000001721*(temperature**2))+(-0.0026739231*temperature)+(1.2612024555) # air density, regression equation with R^2 value of 0.9692103547; data taken from www.EngineeringToolBox.com
	rho_o = 1.225 # kg/m^3, air density at standard atmosphere sea level
	v_ave = windspeed
	v_i = 3. # m/s, cut-in speed
	v_o = 18. # m/s, cut-out speed
	v_r = 13. # m/s, rated speed
	v = v_ave * (rho/rho_o)**(1/3)

	a = v_i**3 / ((v_i**3)-(v_r**3))  # coefficients
	b = 1./((v_r**3)-(v_i**3))  # coefficients


	if v_i <= v <= v_r:
		windPower = installedWind * (a + (b*(v**3)))
	elif v_r <= v <= v_o:
		windPower = installedWind
	else:
		windPower = 0.

	return windPower

def get_solarPower(when, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover,installedPV, arrayEfficiency, inverterEfficiency):
	# This function calculates the output of a solar installation
	latitude = float(latitude)
	longitude = float(longitude)
	altitude = float(altitude)
	tilt = float(tilt)
	azimuth = float(azimuth)
	albedo = float(albedo)
	temperature = float(temperature)
	humidity = float(humidity)
	cloudCover = float(cloudCover)
	installedPV = float(installedPV)
	arrayEfficiency = float(arrayEfficiency)
	inverterEfficiency = float(inverterEfficiency)


	# Predict the solar irradiance
	solarIrradiation = get_GtIsotropic(when, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover) # [W/m^2]

	# method 1
	standardSolarIrradiation = 1000 # watts/m^2
	percentIrradiation = solarIrradiation / standardSolarIrradiation
	solarPower = installedPV * percentIrradiation * inverterEfficiency

	# method 2
	# solarPowerPerSQM = solarIrradiation * arrayEfficiency * inverterEfficiency
	# solarArea = (installedPV/1000) * 10  # 1 kW per 10 sqm for rooftop PV (behind the meter)
	# solarPower = solarPowerPerSQM * solarArea



	return solarPower

# def get_rooftopPV(timestamp, temperature, humidity, cloudCover):
# 	# This function calculates the forecasted output of the rooftop solar PV
# 	when = time.localtime(timestamp)  # convert to time tuple which is required in solar function
# 	buildings =  np.genfromtxt('status_HVAC.csv', delimiter=',', names=True)
# 	pvAdoption = int(len(buildings) * percentPVadoption)
# 	totalOutputRooftopPV = 0.
# 	for i in range(pvAdoption):
# 		latitude = buildings['latitude'][i]
# 		longitude = buildings['longitude'][i]
# 		altitude = buildings['altitude'][i]
# 		tilt = latitude
# 		azimuth = buildings['azimuth'][i]
# 		albedo = buildings['albedo'][i]
# 		solarIrradiance = get_GtIsotropic(when, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover) # [W/m^2]
# 		arrayEfficiency = populate(1,0.10,0.18,0.13)[0] # solar PV conversion efficiency
# 		inverterEfficiency = populate(1,0.85,0.95,0.92)[0] # inverter efficiency
# 		solarArea = buildings['area'][i] * 0.9
# 		outputOfOneBuilding = solarArea * solarIrradiance * arrayEfficiency * inverterEfficiency
# 		totalOutputRooftopPV = totalOutputRooftopPV + outputOfOneBuilding

# 	return totalOutputRooftopPV

def get_DERPower(timestamp, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover, installedPV, arrayEfficiency, inverterEfficiency, windspeed, installedWind):
	# This function calculates expected output from the DERs i.e. solar and wind
	# Parameters:
	#	timestamp = current time in unix format
	#	latitude = site latitude
	# 	longitude = site longitude
	# 	altitude = site elevation
	# 	tilt = tild of the array surface
	# 	azimuth = orientation of the panel with respect to the south
	# 	albedo = ground reflection albedo
	# 	temperature = air temperature
	#	humidity = air humidity from the weather data
	#	cloudCover = cloud covering the area (0--1)
	#	installedPV = installed PV capacity in the area [watts]
	#	arrayEfficiency = average efficiency of the solar array
	#	inverterEfficiency = average efficiency of the inverters
	#	windspeed = speed of the wind based on the weather forecast
	#	temperature = air temperature based on the forecast
	#	installedWind = installed wind power capacity in the area [watts]

	# parameter conversions
	when = time.localtime(int(timestamp))  # convert to time tuple which is required in solar function


	# for the wind
	windPower = get_windPower(installedWind, windspeed, temperature)

	# for the solar plant
	solarPower = get_solarPower(when, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover, installedPV, arrayEfficiency, inverterEfficiency)

	# for the rooftop PV
	# rooftopPV = get_rooftopPV(timestamp, temperature, humidity, cloudCover)

	DERPower = solarPower + windPower #+ rooftopPV

	hourNow = when.tm_hour + (when.tm_min/60.) + (when.tm_sec/3600.)
	# to simulate solar dip
	# if (11.5 < hourNow <= 12.5) and DERMode == 1:
	# 	DERPower = DERPower * 0.2

	return DERPower,windPower,solarPower#,rooftopPV # [watts]


def toUnixTime(stringTime):
	unixtime = time.mktime(datetime.datetime.strptime(stringTime, "%Y-%m-%d %H:%M").timetuple())
	# print (unixtime)
	return unixtime




################# TESTS #################################################################################
# ### Known inputs
# forecastKey = '564ebd21967d3ef7ec6c5d15f588bd26'
# mapAPIkey = 'AIzaSyDHLF0LGjAd9mm0vLmqQfrQuuIjVVHla2k'

# ### User inputs
# latitude = '33.933'
# longitude = '-118.4'
# startTime = toUnixTime('2016-02-16 07:00')
# endTime = toUnixTime('2016-02-17 07:00')

# installedPV = 30000 # watts
# arrayEfficiency = 0.15  # solar PV conversion efficiency
# inverterEfficiency = 0.9 # inverter efficiency
# albedo = 0.2
# tilt = float(latitude)
# azimuth = 0  # facing south

# installedWind = 30000  # watts


# # call functions
# altitude = weather.get_elevation(mapAPIkey, latitude, longitude)
# timezone = weather.get_timezone(mapAPIkey,latitude,longitude,startTime)
# os.environ['TZ'] = timezone
# time.tzset()
# filename = weather.get_weatherHistory(forecastKey, latitude,longitude, startTime, endTime)
# outsideConditions = weather.get_outsideConditions(filename)


# timestamp = toUnixTime('2016-02-16 10:34')
# timeArray = outsideConditions['timestamp']
# sampleIndex = np.where(timeArray==timestamp)
# temperature = float(outsideConditions['temperature'][sampleIndex])
# humidity = float(outsideConditions['relativeHumidity'][sampleIndex])
# cloudCover = float(outsideConditions['cloudCover'][sampleIndex])
# windspeed = float(outsideConditions['windspeed'][sampleIndex])
# temperature = float(outsideConditions['outsideTemp'][sampleIndex])

# a = get_DERPower(timestamp, latitude, longitude, altitude, tilt, azimuth, albedo, temperature, humidity, cloudCover, installedPV, arrayEfficiency, inverterEfficiency, windspeed, installedWind)

# # output
# timeStart = time.localtime(int(startTime))
# timeEnd = time.localtime(int(endTime))
# sampleTime = time.localtime(int(timestamp))


# print ("startTime: " + str(time.strftime('%Y-%m-%d %H:%M' , timeStart)))
# print ("endTime: " + str(time.strftime('%Y-%m-%d %H:%M' , timeEnd)))
# print ("sampleTime: " + str(time.strftime('%Y-%m-%d %H:%M' , sampleTime)))
# print ('Total DER = ' + str(a[0]) + ' watts')
# print ('Wind Power = ' + str(a[1]) + ' watts from installed capacity of ' + str(installedWind) + 'watts' )
# print ('Solar Power = ' + str(a[2]) + ' watts from installed capacity of ' + str(installedPV) + 'watts')
