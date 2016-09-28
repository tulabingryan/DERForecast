""" #############################################################
# Codes to formulate a model to predict solar irradiance using CVXPY
# by: Ryan Tulabing
# LBNL 2015
############################################################# """


import sys
import os
import time
import datetime
import holidays
import solar
import csv
import numpy as np
import math
from scipy import optimize
from pylab import *
import matplotlib.pyplot as plt
import sqlite3 as lite
import glob
from cvxpy import *



# GLOBAL CONSTANTS
Gsc = 1367  # W/m^2, solar energy per unit time per area beyond the atmosphere
albedo = 0.2  # reflection coefficient of the surroundings. Common value is 0.2
e = np.e  # 2.718281828459045  # euler's number
pi = np.pi  # 3.141592653589793  # pi constant


# set receiver orientation
tilt = 0  # degrees from horizontal
azimuth = 0.0  # degrees west of south

alreadySolartime = False  # set true if the given time for simulation is already in solar time



###### Functions for validating the solar models ####################################

##################### TMY ########################################################


# Generate data for Huber regression.
np.random.seed(1)
n = 3 # temperature, humidity, pressure
SAMPLES = 2000 #int(1.5*n)
beta = Variable(n)

# Fetch data from the database
databaseName = 'tmy3.db'
con = lite.connect(databaseName)

with con:
    cur = con.cursor()

    print ('Fetching data from database . . .')
    cur.execute("SELECT tempDryBulb, relativeHumidity, pressure, (ETR-GHI) from TMY where (latitude = 33.933 and longitude = -118.4 and GHI > 0 and ETR > 0) limit "+str(SAMPLES)+"")
    data = np.array(cur.fetchall())

    X = data.T[0:3]

    Y = data.T[3:4].T



# Solve the resulting problems.
# WARNING this script takes a few minutes to run.

""" SOLVER OPTIONS
            LP  SOCP    SDP     EXP     MIP
GLPK        X
GLPK_MI     X                           X
Elemental   X   X
ECOS        X   X               X
ECOS_BB     X   X               X       X
GUROBI      X   X                       X
MOSEK       X   X       X
CVXOPT      X   X       X       X
SCS         X   X       X       X
"""

# solve a least square regression problem.
# print ('Solving least square regression...')
# cost1 = norm(X.T*beta - Y)
# prob = Problem(Minimize(cost1))
# value1 = prob.solve(solver = CVXOPT)
# beta1 = beta.value
# print ('GHI/ETR = ', beta1, " [temperature, humidity, pressure]")
# Y_lsq = beta1.T * X

# fit = norm(Y_lsq - Y)/norm(Y)
# print (fit.value)
# #     lsq_data[idx] = fit.value



# Form and solve the Huber regression problem.
print ('Solving huber regression...')
cost3 = sum_entries(huber(X.T*beta - Y, 1))
prob = Problem(Minimize(cost3))
value3 = prob.solve(solver = CVXOPT)
# huber_data[idx] = fit.value
beta3 = beta.value
print ('GHI/ETR = ', beta3, " [temperature, humidity, pressure]")
Y_huber = beta3.T * X



# #############################################################################

xItem = np.linspace(1, SAMPLES, num=SAMPLES)

# plot for regressions
plt.plot(xItem, Y, '.', label='Actual')
# plt.plot(xItem, Y_lsq.T, '.', label='Standard')
plt.plot(xItem, Y_huber.T, '.', label='Huber')
plt.ylabel('Attenuation, GHI/ETR')
plt.xlabel('Sample')
plt.legend(loc='upper left')
plt.show()


# plot for errors
# plt.plot(xItem, Y-Y_lsq.T, '.', label='Standard')
plt.plot(xItem, Y-Y_huber.T, '.', label='Huber')
plt.ylabel('Error')
plt.xlabel('Sample')
plt.legend(loc='upper left')
plt.show()
