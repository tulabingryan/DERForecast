import django_tables2 as tables
from .models import ForecastDataModel

class SimpleTable(tables.Table):
	time = tables.Column(verbose_name="time")
	solarForecast = tables.Column(verbose_name="solarForecast")
	windForecast = tables.Column(verbose_name="windForecast")
	temperature = tables.Column(verbose_name="temperature")
	humidity = tables.Column(verbose_name="humidity")
	cloudCover = tables.Column(verbose_name="cloudCover")
	class Meta:
		model = ForecastDataModel
		attrs = {"class": "paleblue"}

