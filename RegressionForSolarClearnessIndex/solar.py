#############################################################
# Codes for simulating a Solar PV model
# by: Ryan Tulabing
# LBNL 2015
#############################################################


import sys
import os
import time
import datetime
import csv
import numpy as np
import math
from scipy import optimize
from pylab import *
import glob

# GLOBAL CONSTANTS
Gsc = 1367  # W/m^2, solar energy per unit time per area beyond the atmosphere
albedo = 0.2  # reflection coefficient of the surroundings. Common value is 0.2
e = np.e  # 2.718281828459045  # euler's number
pi = np.pi  # 3.141592653589793  # pi constant

# set location
#latitude = 36.04896164  # degrees, + for North of equator, - for South of Equator
#longitude = -121.20201874  # degrees, + for East of GMT, - for West of GMT
#altitude = 447  # meters

# set receiver orientation
tilt = 0  # degrees from horizontal
azimuth = 0.0  # degrees west of south

# set local timezone
#os.environ['TZ'] = 'GMT+07' # This means 7 hours should be added to local time to reach GMT time
#time.tzset()

# time for testing each function
#daytime = (2011, 2, 3, 6, 50, 0, 0, 0, -1)  # local date and time considering daylight saving
#when = time.mktime(daytime)  # datetime in unix format
#when = time.localtime(when)  # convert to time tuple



alreadySolartime = False  # set true if the given time for simulation is already in solar time


# FUNCTIONS USED

def get_yday(when):
    # This function returns which day of the year is the specific date 'when'
    # Its range is 1 - 365, thus Feb.29 is the same as March 1 in the case of a leap year
    if when.tm_mon == 1:
        n = when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 2:
        n = 31 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 3:
        n = 59 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 4:
        n = 90 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 5:
        n = 120 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 6:
        n = 151 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 7:
        n = 181 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 8:
        n = 212 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 9:
        n = 243 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 10:
        n = 273 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 11:
        n = 304 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    elif when.tm_mon == 12:
        n = 334 + when.tm_mday + (when.tm_hour/24) + (when.tm_min/(60*24)) + (when.tm_sec/(60*24*60))
    return n

def get_climateType(when, latitude):
    # This function returns the type climate in a certain area based solely on its latitude
    # The climate types considered are the types of climate for predicting solar irradiance, by Hottel (1976)
    isSummer = when.tm_isdst
    if abs(latitude) < 23.5:
        climateType = 0  # tropical
    elif 23.5 < abs(latitude) < 66.5:
        if isSummer == 1:
            climateType = 1  # Midlatitude summer
        else:
            climateType = 3  # Midlatitude winter
    elif 66.4 < abs(latitude):
        climateType = 2  # Subarctic summer
    return climateType

def get_solarTime(when, longitude):
    # This function converts a given time from its local timezone into the equivalent solar time.
    if alreadySolartime:
        solarTime = when
    else:
        n = get_yday(when)  # day of the year
        B = (n-1)*(360.0/365.0)
        # time equation, E, Spencer(1971), Iqbal(1983)
        E = 229.2*(0.000075+(0.001868*cos(radians(B)))-(0.032077*sin(radians(B)))\
                    - (0.014615*cos(radians(2*B)))-(0.04089*sin(radians(2*B))))
        unixLocal = time.mktime(when)
        #utcTime = time.gmtime(unixLocal)
        #unixGmt = time.mktime(utcTime)
        meridian = 15 * (time.timezone) / 3600
        if longitude > 0:
            meridian = 360 - meridian
            longitude = 360 - longitude
        else:
            longitude = -1 * longitude
        timeDiff = (4*(meridian-longitude))+E  # time difference in minutes
        timeDiff = datetime.timedelta(minutes=timeDiff)
        localHour = datetime.datetime.fromtimestamp(unixLocal)
        solarTime = localHour + timeDiff
        solarTime = datetime.datetime.timetuple(solarTime)
    return solarTime  # datetime tuple

def get_hourAngle(when, longitude):
    solarTime = get_solarTime(when, longitude)
    solarHour = solarTime.tm_hour + (solarTime.tm_min/60.0) + (solarTime.tm_sec/3600.0)
    # hour angle is the displacement of the sun east or west of the observer's meridian
    # It is 15 degrees per hour, negative values for morning, positive for afternoon
    hourAngle = (solarHour - 12.0)*15.0  # 15 degrees per hour movement of the sun
    return hourAngle  # in degrees

def get_declination(when):
    n = get_yday(when)  # day of the year
    B = (n-1)*(360.0/365.0)
    # solar declination angle, Spencer(1971)... more accurate
    declination = (180/pi)*(0.006918-(0.399912*cos(radians(B)))+(0.070257*sin(radians(B)))\
                            - (0.006758*cos(radians(2*B)))+(0.000907*sin(radians(2*B)))\
                            - (0.002697*cos(radians(3*B)))+(0.00148*sin(radians(3*B))))
    # if estimated value is preferred, uncomment the following lines
    #declination = 23.45*sin(radians(360.0*(284+n)/365))  # approximate version, Cooper(1969)
    return declination  # in degrees

def get_solarAzimuth(when, latitude, longitude):
    hourAngle = get_hourAngle(when, longitude)
    zenithAngle = get_zenithAngle(when, latitude, longitude)
    declination = get_declination(when)
    angleSign = sign(hourAngle)
    a = cos(radians(zenithAngle))
    b = sin(radians(latitude))
    c = sin(radians(declination))
    d = sin(radians(zenithAngle))
    f = cos(radians(latitude))
    solarAzimuth = angleSign * abs(arccos((((a*b)-c)/(d*f))))  # Duffie & Beckman(2013)
    solarAzimuth = degrees(solarAzimuth)
    return solarAzimuth  # in degrees

def get_zenithAngle(when, latitude, longitude):
    declination = get_declination(when)
    hourAngle = get_hourAngle(when, longitude)
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    sunriseHourAngle = sunsetHourAngle * -1
    if sunriseHourAngle < hourAngle < sunsetHourAngle:
        cos_lat = cos(radians(latitude))
        cos_dec = cos(radians(declination))
        cos_w = cos(radians(hourAngle))
        sin_lat = sin(radians(latitude))
        sin_dec = sin(radians(declination))
        zenithAngle = arccos((cos_lat * cos_dec * cos_w)+(sin_lat * sin_dec))  # Duffie & Beckman(2013)
        zenithAngle = degrees(zenithAngle)
    else:
        zenithAngle = 90
    return zenithAngle  # in degrees

def get_solarAltitude(when, latitude, longitude):
    zenithAngle = get_zenithAngle(when, latitude, longitude)
    solarAltitude = 90 - zenithAngle
    return solarAltitude  # in degrees

def get_incidenceAngle(when, latitude, longitude, tilt, azimuth):
    zenithAngle = get_zenithAngle(when, latitude, longitude)
    solarAzimuth = get_solarAzimuth(when, latitude, longitude)

    a = cos(radians(zenithAngle))
    b = cos(radians(tilt))
    c = sin(radians(zenithAngle))
    d = sin(radians(tilt))
    f = cos(radians(solarAzimuth - azimuth))
    incidenceAngle = arccos((a*b) + (c*d*f))  # Duffie & Beckman(2013)
    incidenceAngle = degrees(incidenceAngle)
    return incidenceAngle  # in degrees

def get_sunsetHourAngle(when, latitude):
    declination = get_declination(when)
    a = tan(radians(latitude))
    b = tan(radians(declination))
    sunsetHourAngle = arccos(-1 * a * b)  # Duffie & Beckman(2013)
    sunsetHourAngle = degrees(sunsetHourAngle)
    return sunsetHourAngle  # in degrees

def get_sunriseHourAngle(when, latitude):
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    sunriseHourAngle = -1 * sunsetHourAngle  # Duffie & Beckman(2013)
    return sunriseHourAngle  # in degrees

def get_daylightHours(when, latitude):
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    daylightHours = (2.0/15.0)*sunsetHourAngle  # Duffie & Beckman(2013)
    return daylightHours  # in hours

def get_profileAngle(when, latitude, longitude, azimuth):
    solarAltitude = get_solarAltitude(when, latitude, longitude)
    solarAzimuth = get_solarAzimuth(when, latitude, longitude)
    a = tan(radians(solarAltitude))
    b = cos(radians(solarAzimuth - azimuth))
    profileAngle = arctan(a / b)
    profileAngle = degrees(profileAngle)
    return profileAngle  # in degrees

def get_sunsetHour(when, latitude):
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    sunsetHour = (sunsetHourAngle / 15.0) + 12
    return sunsetHour  # in hour

def get_sunriseHour(when, latitude):
    sunriseHourAngle = get_sunriseHourAngle(when, latitude)
    sunriseHour = (sunriseHourAngle / 15.0) + 12
    return sunriseHour  # in hour

def get_airmass(zenithAngle, altitude):
    # airmass factor, Kaster and Young(1989)
    m = (e**(-0.0001184*altitude))/(cos(zenithAngle)+(0.5057*(96.080-zenithAngle)**(-1.634)))
    return m

def get_oneDaySolar(when, latitude, longitude):
    n = get_yday(when)
    declination = get_declination(when)
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    a = cos(radians(360.0 * n / 365.0))
    b = cos(radians(latitude))
    c = cos(radians(declination))
    d = sin(radians(sunsetHourAngle))
    f = sin(radians(latitude))
    g = sin(radians(declination))
    Ho = (24.0*3600*Gsc/pi)*(1+(0.033*a))*((b*c*d)+(pi*sunsetHourAngle*f*g/180))
    return Ho  # Joules / m^2 per day

def get_solarEnergyT1T2(when, time1, time2, latitude, longitude):

    t1 = time1.split(':')
    t2 = time2.split(':')
    # local date and time considering daylight saving
    daytime1 = (when.tm_year, when.tm_mon, when.tm_mday, int(t1[0]), int(t1[1]), 0, 0, 0, -1)
    when1 = time.mktime(daytime1)
    when1 = time.localtime(when1)
    daytime2 = (when.tm_year, when.tm_mon, when.tm_mday, int(t2[0]), int(t2[1]), 0, 0, 0, -1)
    when2 = time.mktime(daytime2)
    when2 = time.localtime(when2)

    w1 = get_hourAngle(when1, longitude)
    w2 = get_hourAngle(when2, longitude)

    n = get_yday(when)
    declination = get_declination(when)
    a = cos(radians(360.0 * n / 365.0))
    b = cos(radians(latitude))
    c = cos(radians(declination))
    d1 = sin(radians(w1))
    d2 = sin(radians(w2))
    f = sin(radians(latitude))
    g = sin(radians(declination))
    Io = (12.0*3600*Gsc/pi)*(1+(0.033*a))*((b*c*(d2-d1))+(pi*(w2-w1)*f*g/180))
    return Io

def get_outerBeamN(when, latitude, longitude):
    # this function gets the extraterrestrial solar irradiation on a normal plane considering the variations
    # in earth-sun distance throughout the year
    n = get_yday(when)  # day of the year
    B = (n-1) * (360.0/365.0)
    hourAngle = get_hourAngle(when, longitude)
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    sunriseHourAngle = sunsetHourAngle * -1
    #sunsetDif = hourAngle - sunsetHourAngle
    #sunriseDif = hourAngle - sunriseHourAngle


    a = cos(radians(B))
    b = sin(radians(B))
    c = cos(radians(2*B))
    d = sin(radians(2*B))

    #if (0 < sunriseDif < 15):
    #    Gon =  ((sunriseDif)/15)*Gsc * (1.000110+(0.034221*a)+(0.001280*b) + (0.000719*c)+(0.000077*d))  # Iqbal(1983)
    #elif (0 < sunsetDif < 15):
    #    Gon =  ((15 - sunsetDif)/15)*Gsc * (1.000110+(0.034221*a)+(0.001280*b) + (0.000719*c)+(0.000077*d))  # Iqbal(1983)
    if sunriseHourAngle < hourAngle < sunsetHourAngle:
        Gon = Gsc * (1.000110+(0.034221*a)+(0.001280*b) + (0.000719*c)+(0.000077*d))  # Iqbal(1983)
    else:
        Gon = 0.0
    # Below is the estimate version, less accurate
    #Gon = Gsc * (1 + (0.033* cos(radians(360.0*n/365.0))))
    return Gon  # in W/m2, since this is

def get_outerBeamH(when, latitude, longitude):
    # this function gets the extraterrestrial solar irradiation on a horizontal plane considering the variations
    # in earth-sun distance throughout the year
    hourAngle = get_hourAngle(when, longitude)
    sunsetHourAngle = get_sunsetHourAngle(when, latitude)
    sunriseHourAngle = sunsetHourAngle * -1
    if sunriseHourAngle < hourAngle < sunsetHourAngle:
        zenithAngle = get_zenithAngle(when, latitude, longitude)
        Gon = get_outerBeamN(when, latitude, longitude)
        Go = Gon * cos(radians(zenithAngle))
    else:
        Go = 0.0
    return Go  # in W/m^2

def get_clearSkyBeamH(when, latitude, longitude, altitude):
    # This function calculates the direct beam irradiance during clears skies on a Horizontal plane
    # using the method developed by Hottel (1976)
    # Arguments
    #     climateType = 0 if tropical,1 if Midlatitude summer,2 if Subarctic summer,3 if Midlatitude winter
    #    when = the date and time considered
    #    latitude = latitude of the considered location in degrees
    #    longitude = longitude of the considered location in degrees
    #    altitude = height of the location above sea level in meters
    # Returns the direct beam irradiance during clear skies in W/m^2
    climateType = get_climateType(when, latitude)
    Gon = get_outerBeamN(when, latitude, longitude)
    zenithAngle = get_zenithAngle(when, latitude, longitude)
    corrections = [[0.95, 0.98, 1.02], [0.97, 0.99, 1.02], [0.99, 0.99, 1.01], [1.03, 1.01, 1.0]]
    a0 = 0.4237-(0.00821*((6.0-(altitude/1000.0))**2))
    a1 = 0.5055+(0.00595*((6.5-(altitude/1000.0))**2))
    k = 0.2711+(0.01858*((2.5-(altitude/1000.0))**2))
    # applying the correction factors based on climate type
    a0 = a0 * corrections[climateType][0]
    a1 = a1 * corrections[climateType][1]
    k = k * corrections[climateType][2]
    if sin(radians(zenithAngle)) == 0:
        tau_b = a0
    else:
        tau_b = a0 + (a1 * e**(-k/cos(radians(zenithAngle))))
    Gcb = Gon * tau_b * cos(radians(zenithAngle))  # Hottel (1976)
    if Gcb < 0:
        Gcb = 0.0
    return Gcb

def get_clearSkyDiffusedH(when, latitude, longitude, altitude):
    # This function calculates the diffused irradiance during clear skies on a horizontal plane
    # Arguments
    #     climateType = 0 if tropical,1 if Midlatitude summer, 2 if Subarctic summer,3 if Midlatitude winter
    #    when = the date and time considered
    #    latitude = latitude of the considered location in degrees
    #    longitude = longitude of the considered location in degrees
    #    altitude = height of the location above sea level in meters
    # Returns the diffused irradiance during clear skies in W/m^2
    climateType = get_climateType(when, latitude)
    Go = get_outerBeamH(when, latitude, longitude)
    zenithAngle = get_zenithAngle(when, latitude, longitude)
    corrections = [[0.95, 0.98, 1.02], [0.97, 0.99, 1.02], [0.99, 0.99, 1.01], [1.03, 1.01, 1.0]]
    a0 = 0.4237-(0.00821*((6.0-(altitude/1000.0))**2))
    a1 = 0.5055+(0.00595*((6.5-(altitude/1000.0))**2))
    k = 0.2711+(0.01858*((2.5-(altitude/1000.0))**2))
    # applying the correction factors based on climate type
    a0 = a0 * corrections[climateType][0]
    a1 = a1 * corrections[climateType][1]
    k = k * corrections[climateType][2]
    if cos(radians(zenithAngle)) == 0:
        tau_b = a0
    else:
        tau_b = a0 + (a1 * e**(-k/cos(radians(zenithAngle))))
    Gcd = Go * (0.271 - (0.294*tau_b))  # Liu and Jordan (1960)
    if Gcd < 0:
        Gcd = 0.0
    return Gcd

def get_clearSkyH(when, latitude, longitude, altitude):
    # This function determines the total clear sky horizontal irradiance
    beam = get_clearSkyBeamH(when, latitude, longitude, altitude)
    diffused = get_clearSkyDiffusedH(when, latitude, longitude, altitude)
    Gc = beam + diffused
    return Gc

def get_Kt(relativeHumidity):
    # This function determines the clearness index
    # correlation equation was derived by another python code based on the tmy3 database
    Kt = (-4.0609675416664 * (10 ** (-5) * (relativeHumidity**2) ))- (0.0013504072 * relativeHumidity) + 0.7546969703
    return Kt  # clearness index

def get_G(when, latitude, longitude, relativeHumidity):
    Kt = get_Kt(relativeHumidity)
    Go = get_outerBeamH(when, latitude, longitude)
    G = Kt * Go
    return G

def get_Gd(when, latitude, longitude, relativeHumidity):
    G = get_G(when, latitude, longitude, relativeHumidity)
    Kt = get_Kt(relativeHumidity)
    # Orgill and Hollands correlation
    if Kt <= 0.35:
        Gd = G*(1.0 - (0.249*Kt))
    elif 0.35 < Kt <= 0.75:
        Gd = G*(1.557 - (1.84*Kt))
    elif Kt > 0.75:
        Gd = G*0.177
    return Gd

def get_Gb(when, latitude, longitude, relativeHumidity):
    G = get_G(when, latitude, longitude, relativeHumidity)
    Gd = get_Gd(when, latitude, longitude, relativeHumidity)
    Gb = G - Gd
    return Gb

def get_GtIsotropic(when, latitude, longitude, altitude, tilt, azimuth, albedo, relativeHumidity):
    # This function calculates the irradiance on a tilted plane using the isotropic model
    incidenceAngle = get_incidenceAngle(when, latitude, longitude, tilt, azimuth)
    G = get_G(when, latitude, longitude, relativeHumidity)
    Gb = get_Gb(when, latitude, longitude, relativeHumidity)
    Gd = get_Gd(when, latitude, longitude, relativeHumidity)
    rho_g = albedo  # albedo reflection factor
    Gt = (Gb) + (Gd*0.5*(1+cos(radians(tilt)))) + (G*rho_g*0.5*(1-cos(radians(tilt))))
    return Gt

def get_Rb(when, latitude, longitude, tilt, azimuth):
    # This function calculates the ratio of solar radiation on a tilted surface and a horizontal surface
    incidenceAngle = get_incidenceAngle(when,latitude,longitude,tilt, azimuth)
    zenithAngle = get_zenithAngle(when, latitude, longitude)

    cos_inc = sin(radians(incidenceAngle))
    cos_zen = cos(radians(zenithAngle))

    Rb = cos_inc / cos_zen
    return Rb

def get_GtHDKR(when, latitude, longitude, altitude, tilt, azimuth, albedo, relativeHumidity):
    # This function uses the model of Hay, Davies, Klucher, and Reindl (HDKR)
    # to forecast the available solar radiation for 1 hour interval
    rho_g = albedo
    Go = get_outerBeamH(when, latitude, longitude)
    Gb = get_Gb(when, latitude, longitude, relativeHumidity)
    Gd = get_Gd(when, latitude, longitude, relativeHumidity)
    G = get_G(when, latitude, longitude, relativeHumidity)
    if Go > 0:
        Ai = Gb / Go
        f = sqrt(Gb/G)
    else:
        Ai = 0.0
        f = 0.0
    Rb = get_Rb(when, latitude, longitude, tilt, azimuth)

    Gt = ((Gb + (Gd*Ai))*Rb) + (Gd*(1-Ai)*(0.5*(1+cos(radians(tilt))))*(1+(f*((sin(radians(0.5*tilt)))**3))))\
        +(G*rho_g*0.5*(1-cos(radians(tilt))))
    if Gt < 0:
        Gt = 0.0
    return Gt


def get_haziness(visibility):
    # This function converts the given visibility to haziness
    # From the Koshmeider equation: visibility = 3.912/ extinction coefficient
    # At sea level, Rayleigh's atmosphere (the cleanest possible) has an extinction coefficient of 13.2x10^-6 m^-1 at 520nm wavelength
    # so, visibility limit is 296 km.
    # Parameter: visibility = data from weather station in meters
    for i in range(0,len(visibility)):
        if visibility[i] > 296000:
            visibility[i] = 296000

    haziness = (296000 - visibility) / 296000
    return haziness
