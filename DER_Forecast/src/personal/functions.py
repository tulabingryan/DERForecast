import datetime
import time
# import urllib2  # for python2 build
import csv
import numpy as np
import os
from dateutil.parser import parse
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
import json
import pandas as pd
import numpy as np
from .DER import *

# API keys
forecastKey = '564ebd21967d3ef7ec6c5d15f588bd26'  # for darkskyio weather api
mapAPIkey = 'AIzaSyDHLF0LGjAd9mm0vLmqQfrQuuIjVVHla2k'  # for googlemap api


# Get site location coordinates: latitude and longitude
googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'


def get_coordinates(query, from_sensor=False):
    query = query.encode('utf-8')
    params = {
        'address': query,
        'sensor': "true" if from_sensor else "false"
    }

    req = googleGeocodeUrl + urlencode(params)
    response = urlopen(req)
    respData = response.read()
    respData = respData.decode("utf-8")
    # print (respData)
    response = json.loads(respData)
    if response['results']:
        location = response['results'][0]['geometry']['location']
        latitude, longitude = location['lat'], location['lng']
        # print (query, latitude, longitude)

    else:
        latitude, longitude = None, None
        print (query, "<no results>")
    return latitude, longitude


def get_elevation(mapAPIkey, latitude, longitude):
    '''
    This function determines the elevation of the location specified by latitude and longitude
    '''

    # fetching data using python3
    url = 'https://maps.googleapis.com/maps/api/elevation/json?locations=' + str(latitude) + ',' + str(longitude) + '&key=' + str(mapAPIkey)
    req = Request(url)
    try:
        response = urlopen(req)
        respData = response.read()
        respData = respData.decode("utf-8")
        # print (respData)
        parsed_json = json.loads(respData)
        # print (parsed_json)
        elevation = parsed_json["results"][0]["elevation"]  # get the elevation
        # print('Location: latitude ' + str(latitude) + ", longitude " + str(longitude))
        # print ("Elevation: " + str(elevation))
        response.close()

    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
    else:
        print("Unknown error.")  # everything is fine



    return str(elevation)

def get_timezone(mapAPIkey,latitude,longitude,timestamp):
    '''
    This function determines the timezone in the location specified by the latitude and longitude
    '''

    global timezone

    ###### fetching data using python3
    url = 'https://maps.googleapis.com/maps/api/timezone/json?location=' + str(latitude) + ',' + str(longitude) + '&timestamp=' + str(timestamp) + '&key=' + str(mapAPIkey)
    req = Request(url)
    try:
        response = urlopen(req)
        respData = response.read()
        respData = respData.decode("utf-8")
        # print (respData)
        parsed_json = json.loads(respData)
        # print (parsed_json)
        timezone = parsed_json['timeZoneId']  # get timezone
        # print("latitude: "+ latitude)
        # print("longitude: "+ longitude)
        # print ("timezone: "+ timezone)

        response.close()

        # adjust timezone setting used for runtime
        os.environ['TZ'] = timezone
        time.tzset()
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
    else:
        print("Unknown Error")  # everything is fine
    return timezone


def get_weatherHistory(api_key, latitude, longitude, startTime, endTime):
    '''this function returns a csv file with weather conditions within the specified startTime and endTime times
    '''
    global timezone

    start = datetime.datetime.fromtimestamp(int(startTime))
    end = datetime.datetime.fromtimestamp(int(endTime))

    dateSeries = pd.date_range(start=start, end=end, freq='D', normalize=False)


    weatherData = pd.DataFrame()  # empty holder of weather data

    print ('Fetching weather data . . .')
    for date in dateSeries:
        # Collect past weather condition using Dark Sky Forecast API for specified location and timestamp
        # in SI units, using specified API key

        timestamp = datetime.datetime.timetuple(date)
        timestamp = str(int(time.mktime(timestamp)))
        # print(timestamp)

        #### fetch weather data using python3
        url = 'https://api.forecast.io/forecast/' + api_key + '/' + str(latitude) + ',' + str(longitude) + ','+ str(timestamp) + '?units=si'
        req = Request(url)
        try:
            response = urlopen(req)
            respData = response.read()
            respData = respData.decode("utf-8")
            # print (respData)
            parsed_json = json.loads(respData)
            # print (parsed_json)
            ############################

            timezone = parsed_json['timezone']  # to get the hourly conditions
            # print(timezone)
            #currently_ob = parsed_json['currently']  # to get the current condition only
            hourly_ob = parsed_json['hourly']  # to get the hourly conditions
            # daily_ob = parsed_json['daily']  # to get the daily condition
            # localTime = float(timestamp)
            # localTime = datetime.datetime.timetuple(currentDate) # time.localtime(localTime)

            data = pd.DataFrame(hourly_ob['data'])
            # print("dataShape:", data.shape)
            weatherData = weatherData.append(data)
            # print("weatherDataShape:", weatherData.shape)

        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        else:
            print("Fetching. . . " + str(date)) # everything is fine

        response.close()

    weatherData['time'] = pd.to_datetime(weatherData['time'],unit='s')
    weatherData = weatherData.set_index(['time'])
    weatherData.index = weatherData.index.tz_localize('UTC').tz_convert(timezone)
    # print(weatherData)

    # ### write to csv file
    # filename = 'hourlyWeather.csv'
    # weatherData.to_csv(filename, sep=',', encoding='utf-8')

    # ### interpollate for per minute values
    # minuteSeries = pd.date_range(start=start, end=end, freq='Min', normalize = False, tz=timezone)
    # weatherData = weatherData.reindex(minuteSeries)
    # weatherData = weatherData.apply(pd.Series.interpolate)
    # print(weatherData)

    ### write to csv file
    # filename = 'minutelyWeather.csv'
    # weatherData.to_csv(filename, sep=',', encoding='utf-8')

    return weatherData



def get_weatherHistoryNow(api_key, latitude, longitude):
    '''this function returns a csv file with weather conditions
    # Current conditions
    # Minute-by-minute forecasts out to 1 hour (where available)
    # Hour-by-hour forecasts out to 48 hours
    # Day-by-day forecasts out to 7 days
    # in SI units, using specified API key
    '''

    global timezone

    weatherData = pd.DataFrame()  # empty holder of weather data

    print ('Fetching weather data . . .')

    #### Collect realtime weather condition using Dark Sky Forecast API
    url = 'https://api.forecast.io/forecast/' + api_key + '/' + str(latitude) + ',' + str(longitude) + '?units=si'
    req = Request(url)
    try:
        response = urlopen(req)
        respData = response.read()
        respData = respData.decode("utf-8")
        parsed_json = json.loads(respData)

        timezone = parsed_json['timezone']  # gets the timezone
        # print(timezone)
        #currently_ob = parsed_json['currently'] #to get the current condition
        hourly_ob = parsed_json['hourly']  # to get the hourly conditions
        # daily_ob = parsed_json['daily']  # to get the daily condition
        data = pd.DataFrame(hourly_ob['data'])
        weatherData = weatherData.append(data)

    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
    else:
        print("Fetching data. . . " ) # everything is fine

    response.close()

    weatherData['timezone'] = timezone

    weatherData['time'] = pd.to_datetime(weatherData['time'],unit='s')
    start = weatherData['time'][0]
    end = weatherData['time'][len(weatherData)-1]

    # print(start, end)
    # print(weatherData['time'])

    # set time column as index
    weatherData = weatherData.set_index(['time'])
    weatherData.index = weatherData.index.tz_localize('UTC').tz_convert(timezone)
    # print(weatherData.index)

    ### write to csv file
    filename = 'hourlyWeather.csv'
    weatherData.to_csv(filename, sep=',', encoding='utf-8', header = True)

    ### interpollate for per minute values
    # minuteSeries = pd.date_range(start=start, end=end, freq='Min', normalize = False, tz=timezone)
    # weatherData = weatherData.reindex(minuteSeries)
    # weatherData = weatherData.apply(pd.Series.interpolate)
    # print(weatherData)

    ### write to csv file
    # filename = 'minutelyWeather.csv'
    # weatherData.to_csv(filename, sep=',', encoding='utf-8')

    return weatherData

def getDataFromCSV():

    data = pd.DataFrame.from_csv('hourlyWeather.csv', header=0, sep=',', index_col=0, parse_dates=True, encoding='utf-8', tupleize_cols=False, infer_datetime_format=True)


    return data


def processDataSolar(row):
    # preconditioning of variables
    timezone =  row['timezone']
    os.environ['TZ'] = timezone
    time.tzset()
    timeIndex = row.name
    timestamp = datetime.datetime.timetuple(timeIndex)
    temperature = row['temperature']
    humidity = row['humidity']
    cloudCover = row['cloudCover']
    windspeed = row['windSpeed']

    latitude = row['latitude']
    longitude = row['longitude']
    installed_PV = row['installed_PV']
    array_Efficiency = row['array_Efficiency']
    inverter_Efficiency = row['inverter_Efficiency']
    installed_Wind = row['installed_Wind']
    tilt = row['tilt']
    azimuth = row['azimuth']
    albedo = row['albedo']
    elevation = row['elevation']


    solar = get_solarPower(timestamp, latitude, longitude, elevation, tilt, azimuth, albedo, temperature, humidity, cloudCover,installed_PV, array_Efficiency, inverter_Efficiency)

    return solar

def processDataWind(row):
    # preconditioning of variables
    timezone =  row['timezone']
    os.environ['TZ'] = timezone
    time.tzset()
    timeIndex = row.name
    timestamp = datetime.datetime.timetuple(timeIndex)
    temperature = row['temperature']
    humidity = row['humidity']
    cloudCover = row['cloudCover']
    windspeed = row['windSpeed']

    latitude = row['latitude']
    longitude = row['longitude']
    installed_PV = row['installed_PV']
    array_Efficiency = row['array_Efficiency']
    inverter_Efficiency = row['inverter_Efficiency']
    installed_Wind = row['installed_Wind']
    tilt = row['tilt']
    azimuth = row['azimuth']
    albedo = row['albedo']
    elevation = row['elevation']

    wind = get_windPower(installed_Wind, windspeed, temperature)
    return wind


def forecast(data):
    print("Processing data...")

    data['solarForecast'] = data.apply(processDataSolar, axis='columns', raw=True)
    data['windForecast'] = data.apply(processDataWind, axis='columns', raw=True)

    return data



