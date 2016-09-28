from .functions import *  # import functions for forecasting
from django.shortcuts import render
from .forms import SolarSettingsForm,WindSettingsForm,SiteParametersForm,TimePeriodForm,POI
from .models import ForecastDataModel
from .tables import SimpleTable
from django_tables2 import RequestConfig

# from bokeh.plotting import figure
# from bokeh.models import Range1d, ColumnDataSource, DatetimeTickFormatter
from bokeh.embed import components
# from bokeh.resources import CDN
from bokeh.charts import TimeSeries, Area
from bokeh.layouts import row
# from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
# from bokeh.io import output_file, show, vform


# from urllib.error import URLError, HTTPError
# from chartit import DataPool, Chart

# import datetime
import time
from .DER import *


# API keys
forecastKey = '564ebd21967d3ef7ec6c5d15f588bd26'  # for darkskyio weather api
mapAPIkey = 'AIzaSyDHLF0LGjAd9mm0vLmqQfrQuuIjVVHla2k'  # for googlemap api


# Create your views here.
def index(request):
    form = POI(request.POST or None)
    title = 'Get started'
    instruction = 'Please enter the site location.'
    context = {
        "title": title,
        "instruction": instruction,
        "form": form,
    }

    return render(request, 'personal/home.html', context)


def settings(request):
    global timezone

    timestamp = time.time()
    latitude = request.POST['location_0']
    longitude = request.POST['location_1']
    # context = {}
    if not (latitude == "" or longitude == ""):
        link = "personal/settings.html"
        elevation = get_elevation(mapAPIkey, latitude, longitude)
        print('elevation:', elevation)
        timezone = get_timezone(mapAPIkey, latitude, longitude, timestamp)
        # print('timezone:', timezone)

        # print(datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M'))

        # get weather conditions and write into a csv file
        outsideConditions = get_weatherHistoryNow(forecastKey, latitude, longitude)
        # print(outsideConditions)

        formWind = WindSettingsForm(initial={
            'installed_Wind': 4.0,
        })

        formSolar = SolarSettingsForm(initial={
            'installed_PV': 4.0,
            'array_Efficiency': 0.15,
            'inverter_Efficiency': 0.85,
            'tilt': latitude,
            'azimuth': 0.0,
        })

        formSite = SiteParametersForm(initial={
            'albedo': 0.2,
            'elevation': elevation,
            'latitude': latitude,
            'longitude': longitude
        })

        title = "Settings"
        instruction = 'Please provide the details of the installed DER.'
        context = {
            "title": title,
            "instruction": instruction,
            "formSolar": formSolar,
            "formWind": formWind,
            "formSite": formSite
        }

        print(context)
        # if form1.is_valid() and form2.is_valid():
        #   location = form.cleaned_data.get("location")
    else:
        link = 'personal/home.html'
        form = POI(request.POST or None)
        title = 'Get started'
        instruction = 'Please enter the site location.'
        context = {
            "title": title,
            "instruction": instruction,
            "form": form,
        }

    return render(request, link, context)


def charts(request):
    # print(request.POST)
    latitude = request.POST['latitude']
    longitude = request.POST['longitude']
    # installed_PV = request.POST['installed_PV']
    # array_Efficiency = request.POST['array_Efficiency']
    # inverter_Efficiency = request.POST['inverter_Efficiency']
    # installed_Wind = request.POST['installed_Wind']
    # tilt = request.POST['tilt']
    # azimuth = request.POST['azimuth']
    # albedo = request.POST['albedo']
    # elevation = request.POST['elevation']
    timestamp = time.time()
    timezone = get_timezone(mapAPIkey, latitude, longitude, timestamp)

    data = getDataFromCSV()
    # print(data.index)
    # data.index = data.index.tz_localize('UTC').tz_convert(timezone)
    # print(data.index)

    data['latitude'] = request.POST['latitude']
    data['longitude'] = request.POST['longitude']
    data['installed_PV'] = request.POST['installed_PV']
    data['array_Efficiency'] = request.POST['array_Efficiency']
    data['inverter_Efficiency'] = request.POST['inverter_Efficiency']
    data['installed_Wind'] = request.POST['installed_Wind']
    data['tilt'] = request.POST['tilt']
    data['azimuth'] = request.POST['azimuth']
    data['albedo'] = request.POST['albedo']
    data['elevation'] = request.POST['elevation']

    data = forecast(data)

    data = data.reset_index(level=None, drop=False,
                            inplace=False, col_level=0, col_fill='')
    # print(data['time'], data['solarForecast'])

    tableData = pd.DataFrame(
        data, columns=['time', 'solarForecast', 'windForecast'])
    # tableData = tableData.to_dict(orient='index')
    print(tableData['time'])
    print(tableData)

    # adjust timezone setting used for runtime
    os.environ['TZ'] = timezone
    time.tzset()

    # Original plot for timeseries
    tsline = Area(data, x='time', y=['solarForecast','windForecast'],
                        color=['solarForecast','windForecast'],
                        dash=['solarForecast','windForecast'],
                        title="FORECAST",
                        ylabel='Power(kW)',
                        legend=False)

    tsline1 = Area(data, x='time', y=['solarForecast'],
                        color=['solarForecast'],
                        dash=['solarForecast'],
                        title="SOLAR FORECAST",
                        ylabel='Power(kW)',
                        legend=False)


    tsline2 = Area(data, x='time', y=['windForecast'],
                        color=['blue'],
                        dash=['windForecast'],
                        title="WIND FORECAST",
                        ylabel='Power(kW)',
                        legend=False)


    plot = row(tsline1, tsline2)
    script, div = components(plot)  # wrap_script=True, wrap_plot_info=True)

    # # for displaying the table
    # tableData = dict(
    #     TIME=data['time'],
    #     SOLAR=data['solarForecast'],
    #     WIND=data['windForecast'],
    # )

    tableHeader = {'headers': ['TIME', 'SOLAR', 'WIND']}
    # print(tableData)

    # source = ColumnDataSource(data)
    # columns = [
    #   TableColumn(field="time",title="TIMESTAMP"),
    #   TableColumn(field="solarForecast", title="SOLAR FORECAST"),
    #   TableColumn(field="windForecast", title="WIND FORECAST")
    #   ]

    # data_table = DataTable(source=source, columns=columns, width=400)

    # table = vform(data_table)
    # table_script, table_div = components(table)

    # print(columns)
    # print(table_script)
    # print(table_div)
    context = {
        'the_script': script,
        'the_div': div,
        # 'table_script': table_script,
        # 'table_div': table_div,
        'tableHeader': tableHeader,
        'tableData': tableData.T
    }

    # dataModel = ForecastDataModel()

    # def saveToModel(row):
    #   dataModel.time = row['time']
    #   dataModel.solarForecast = row['solarForecast']
    #   dataModel.windForecast = row['windForecast']
    #   dataModel.temperature = row['temperature']
    #   dataModel.humidity = row['humidity']
    #   dataModel.cloudCover = row['cloudCover']
    #   dataModel.save()

    # data.apply(saveToModel, axis='columns', raw=True)
    # print(dataModel.time)
    # print(dataModel.solarForecast)
    # print(dataModel.windForecast)
    # print(dataModel.temperature)
    # print(dataModel.humidity)
    # print(dataModel.cloudCover)

    # For the table
    # tableQuery = ForecastDataModel.objects.all()
    # table = SimpleTable(tableQuery)
    # RequestConfig(request).configure(table)

    # tableData = pd.DataFrame()
    # tableData['time'] = data['time']
    # tableData['solarForecast'] = data['solarForecast']
    # tableData['windForecast'] = data['windForecast']
    # print(tableData)

    # ### for the graph
    # forecastdata = DataPool(series=
    #           [{'options': {
    #               'source': ForecastDataModel.objects.all()},
    #           'terms': [
    #               'time',
 #                      'solarForecast',
 #                      'windForecast']}

 #                  ])

    # cht = Chart( datasource = forecastdata,
    #   series_options = [{'options':{'type': 'line', 'stacking': False},
    #   'terms':{'time': ['solarForecast', 'windForecast']}}],
    #   chart_options = {'title': {'text': 'DER Forecast'},
    #   'xAxis': {'title': {'text': 'Timestamp'}}, 'yAxis':{'title':{'text':'Output Power (kW)'}}})
    # context = {
    #   'forecastchart': cht,
    #   'tableData': tableData
    #   }

    # dataModel.delete()

    return render(request, 'personal/charts.html', context)


def contact(request):
    return render(request, 'personal/basic.html', {'content': ['To contact the developer, please send an email to:', 'tulabingryan@yahoo.com']})


def simplechart(request):
    # read in some stock data from the Yahoo Finance API
    data = getDataFromCSV()
    dataDict = dict(
        time=data['Adj Close'],
        Date=AAPL['Date'],
        MSFT=MSFT['Adj Close'],
        IBM=IBM['Adj Close'],
    )

    tsline = TimeSeries(data, x='Date', y=['IBM', 'MSFT', 'AAPL'],
                        color=['IBM', 'MSFT', 'AAPL'],
                        dash=['IBM', 'MSFT', 'AAPL'],
                        title="Timeseries", ylabel='Stock Prices', legend=True)

    # tspoint = TimeSeries(data,
    #     x='Date', y=['IBM', 'MSFT', 'AAPL'],
    #     color=['IBM', 'MSFT', 'AAPL'], dash=['IBM', 'MSFT', 'AAPL'],
    #     builder_type='point', title="Timeseries Points",
    #     ylabel='Stock Prices', legend=True)

    # output_file("timeseries.html")
    plot = vplot(tsline)
    script, div = components(plot, wrap_script=True, wrap_plot_info=True)

    # # create some data
    # x1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # y1 = [0, 8, 2, 4, 6, 9, 5, 6, 25, 28, 4, 7]
    # x2 = [2, 5, 7, 15, 18, 19, 25, 28, 9, 10, 4]
    # y2 = [2, 4, 6, 9, 15, 18, 0, 8, 2, 25, 28]
    # x3 = [0, 1, 0, 8, 2, 4, 6, 9, 7, 8, 9]
    # y3 = [0, 8, 4, 6, 9, 15, 18, 19, 19, 25, 28]

    # # select the tools we want
    # TOOLS="pan,wheel_zoom,box_zoom,reset,save"

    # # the red and blue graphs will share this data range
    # xr1 = Range1d(start=0, end=30)
    # yr1 = Range1d(start=0, end=30)

    # # only the green will use this data range
    # xr2 = Range1d(start=0, end=30)
    # yr2 = Range1d(start=0, end=30)

    # # build our figures
    # p1 = figure(x_range=xr1, y_range=yr1, tools=TOOLS, plot_width=300, plot_height=300)
    # p1.scatter(x1, y1, size=12, color="red", alpha=0.5)

    # p2 = figure(x_range=xr1, y_range=yr1, tools=TOOLS, plot_width=300, plot_height=300)
    # p2.scatter(x2, y2, size=12, color="blue", alpha=0.5)

    # p3 = figure(x_range=xr2, y_range=yr2, tools=TOOLS, plot_width=300, plot_height=300)
    # p3.scatter(x3, y3, size=12, color="green", alpha=0.5)

    # # plots can be a single Bokeh Model, a list/tuple, or even a dictionary
    # plots = {'Red': p1, 'Blue': p2, 'Green': p3}

    # script, div = components(plot)
    print(script)
    print(div)

    return render(request, "personal/simplechart.html", {"the_script": script, "the_div": div})
