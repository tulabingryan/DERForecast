from django import forms

from .models import PointOfInterest  # SolarSettingsModel, WindSettingsModel


class POI(forms.ModelForm):
    class Meta:
        model = PointOfInterest
        fields = ['location']


class SolarSettingsForm(forms.Form):
    installed_PV = forms.FloatField()
    array_Efficiency = forms.FloatField()
    inverter_Efficiency = forms.FloatField()
    tilt = forms.FloatField()
    azimuth = forms.FloatField()

    # class Meta:
    #   model = SolarSettingsModel
    #   fields = ['installed_PV', 'array_Efficiency', 'inverter_Efficiency','tilt', 'azimuth', 'albedo', 'elevation', 'latitude', 'longitude']


class SiteParametersForm(forms.Form):
    elevation = forms.FloatField()
    albedo = forms.FloatField()
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())


class WindSettingsForm(forms.Form):
    installed_Wind = forms.FloatField()
    # class Meta:
    #   model = WindSettingsModel
    #   fields = ['installed_Wind']


class TimePeriodForm(forms.Form):
    startTime = forms.DateTimeField()
    endTime = forms.DateTimeField()

