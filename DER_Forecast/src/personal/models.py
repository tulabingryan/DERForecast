from django.db import models
from geoposition.fields import GeopositionField
from django_pandas.managers import DataFrameManager
from picklefield.fields import PickledObjectField


# Create your models here.
class PointOfInterest(models.Model):
    location = GeopositionField()
    name = models.CharField(max_length=100)

# class SolarSettingsModel(models.Model):
#   installed_PV = models.FloatField()
#   array_Efficiency = models.FloatField()
#   inverter_Efficiency = models.FloatField()
#   latitude = models.FloatField()
#   longitude = models.FloatField()
#   elevation = models.FloatField()
#   tilt = models.FloatField()
#   azimuth = models.FloatField()
#   albedo = models.FloatField()

# class WindSettingsModel(models.Model):
#   installed_Wind = models.FloatField()


class ForecastDataModel(models.Model):
    # time = PickledObjectField()
    # solarForecast = PickledObjectField()
    # windForecast = PickledObjectField()
    # temperature = PickledObjectField()
    # humidity = PickledObjectField()
    # cloudCover = PickledObjectField()
    # objects = DataFrameManager()
    time = models.DateTimeField()
    solarForecast = models.FloatField()
    windForecast = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    cloudCover = models.FloatField()
