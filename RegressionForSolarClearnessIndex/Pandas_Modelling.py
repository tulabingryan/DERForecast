""" #############################################################
Codes to formulate a model to predict solar irradiance using Pandas
by: Ryan Tulabing
LBNL 2015
############################################################# """


import sys
import os
import time
import datetime
import solar
import csv
import numpy as np
import math
from scipy import optimize
from pylab import *
import matplotlib.pyplot as plt
import sqlite3 as lite
import glob
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn import metrics



# GLOBAL CONSTANTS
Gsc = 1367  # W/m^2, solar energy per unit time per area beyond the atmosphere
albedo = 0.2  # reflection coefficient of the surroundings. Common value is 0.2
e = np.e  # 2.718281828459045  # euler's number
pi = np.pi  # 3.141592653589793  # pi constant


# set receiver orientation
tilt = 0  # degrees from horizontal
azimuth = 0.0  # degrees west of south

alreadySolartime = False  # set true if the given time for simulation is already in solar time



### Auxilliary functions ###
def writeToCSV(dataToWrite,csvFilename,header):
    # This function writes data in a csv file
    # Parameters:
    #   dataToWrite = array containing the data to be written
    #   csvFilename = the filename of the csv file
    #   header = a tuple of words representing the headers for the csv file

    fileToWrite = open(csvFilename, 'wt')
    writer = csv.writer(fileToWrite)
    writer.writerow(header)
    for i in range(0,len(dataToWrite)):
        newList = dataToWrite[i]
        writer.writerow(newList)
    fileToWrite.close()
    return






### Fetch data from the database ###
# uncomment the following lines to get new sets of data from the database
# databaseName = 'tmy3.db'
# con = lite.connect(databaseName)

# header = ["DOY", "time", "temperature", "humidity", "pressure", "windspeed", "cloudCoverTotal", "attenuation"]

# with con:
#     cur = con.cursor()

#     print ('Fetching data from database . . .')
#     cur.execute("SELECT DOY, time, tempDryBulb, relativeHumidity, pressure, windspeed, cloudCoverTotal, (GHI/ETR) from TMY where (latitude = 33.933 and longitude = -118.4 and GHI > 0 and ETR > 0)")  # limit "+str(SAMPLES)+"")
#     data = np.array(cur.fetchall())

#     writeToCSV(data, 'rawData.csv', header)
#     print("Finished writing data to: rawData.csv")


### Regression using pandas

data = pd.read_csv("rawData.csv")
Y = data['attenuation']

# accounting temperature, humidity and cloudCover
feature_cols = ['temperature', 'humidity', 'cloudCoverTotal']
X = data[feature_cols]

# accounting only humidity and windspeed
feature_cols2 = ['humidity', 'cloudCoverTotal']
X2 = data[feature_cols2]

# accounting only temperature and humidity
feature_cols3 = ['temperature', 'humidity']
X3 = data[feature_cols3]

# accounting only temperature and windspeed
feature_cols4 = ['temperature', 'cloudCoverTotal']
X4 = data[feature_cols4]

# accounting only temperature
feature_cols5 = ['temperature']
X5 = data[feature_cols5]

# accounting only humidity
feature_cols6 = ['humidity']
X6 = data[feature_cols6]

# accounting only humidity
feature_cols7 = ['cloudCoverTotal']
X7 = data[feature_cols7]


# split data into training and testing data
from sklearn.cross_validation import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(X,Y, random_state=1)

X2_train, X2_test, Y2_train, Y2_test = train_test_split(X2,Y, random_state=1)

X3_train, X3_test, Y3_train, Y3_test = train_test_split(X3,Y, random_state=1)

X4_train, X4_test, Y4_train, Y4_test = train_test_split(X4,Y, random_state=1)

X5_train, X5_test, Y5_train, Y5_test = train_test_split(X5,Y, random_state=1)

X6_train, X6_test, Y6_train, Y6_test = train_test_split(X6,Y, random_state=1)

X7_train, X7_test, Y7_train, Y7_test = train_test_split(X7,Y, random_state=1)


# find coefficient of the regression model
linreg = LinearRegression()
linreg.fit(X_train, Y_train)
print (linreg.intercept_, linreg.coef_)

linreg2 = LinearRegression()
linreg2.fit(X2_train, Y2_train)
print (linreg2.intercept_, linreg2.coef_)

linreg3 = LinearRegression()
linreg3.fit(X3_train, Y3_train)
print (linreg3.intercept_, linreg3.coef_)

linreg4 = LinearRegression()
linreg4.fit(X4_train, Y4_train)
print (linreg4.intercept_, linreg4.coef_)

linreg5 = LinearRegression()
linreg5.fit(X5_train, Y5_train)
print (linreg5.intercept_, linreg5.coef_)

linreg6 = LinearRegression()
linreg6.fit(X6_train, Y6_train)
print (linreg6.intercept_, linreg6.coef_)

linreg7 = LinearRegression()
linreg7.fit(X7_train, Y7_train)
print (linreg7.intercept_, linreg7.coef_)

### predictions ###
Y_predict = linreg.predict(X_test)
Y2_predict = linreg2.predict(X2_test)
Y3_predict = linreg3.predict(X3_test)
Y4_predict = linreg4.predict(X4_test)
Y5_predict = linreg5.predict(X5_test)
Y6_predict = linreg6.predict(X6_test)
Y7_predict = linreg7.predict(X7_test)


### test the model ###
RMSE = np.sqrt(metrics.mean_squared_error(Y_test, Y_predict))
RMSE2 = np.sqrt(metrics.mean_squared_error(Y2_test, Y2_predict))
RMSE3 = np.sqrt(metrics.mean_squared_error(Y3_test, Y3_predict))
RMSE4 = np.sqrt(metrics.mean_squared_error(Y4_test, Y4_predict))
RMSE5 = np.sqrt(metrics.mean_squared_error(Y5_test, Y5_predict))
RMSE6 = np.sqrt(metrics.mean_squared_error(Y6_test, Y6_predict))
RMSE7 = np.sqrt(metrics.mean_squared_error(Y7_test, Y7_predict))

# print the root mean square error
print("RMSE = "+str(RMSE))  #
print("RMSE2 = "+str(RMSE2))
print("RMSE3 = "+str(RMSE3))
print("RMSE4 = "+str(RMSE4))
print("RMSE5 = "+str(RMSE5))
print("RMSE6 = "+str(RMSE6))
print("RMSE7 = "+str(RMSE7))



### Plots ###
# parameters vs the attenuation
g = sns.jointplot('temperature', 'attenuation', data=data, kind='reg')
g = sns.jointplot('humidity', 'attenuation', data=data, kind='reg')
g = sns.jointplot('windspeed', 'attenuation', data=data, kind='reg')
g = sns.jointplot('cloudCoverTotal', 'attenuation', data=data, kind='reg')


# g = sns.pairplot(data, x_vars=["temperature", "humidity", "windspeed"], y_vars= "attenuation", kind='reg')

# actual vs predicted
xItem = np.linspace(1, len(Y_predict), num=len(Y_test))
error = Y_predict - Y_test
data2 = np.vstack((xItem, Y_predict, Y2_predict, Y3_predict, Y4_predict, Y5_predict, Y6_predict, Y7_predict, Y_test, error)).T
data2 = pd.DataFrame(data2)
data2.columns = ['xItem', 'ClearnessPredicted', 'Y2_predict', 'Y3_predict', 'Y4_predict', 'Y5_predict', 'Y6_predict', 'Y7_predict', 'ClearnessActual', 'error']
g = sns.jointplot('ClearnessPredicted', 'ClearnessActual', data=data2, kind='reg')
g = sns.jointplot('ClearnessPredicted', 'ClearnessActual', data=data2, kind='resid')


plt.show()


