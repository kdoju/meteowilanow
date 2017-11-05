from flask import Flask, render_template, request, redirect, url_for
from flask_mobility import Mobility
from flask_bootstrap import Bootstrap
import pandas as pd
import MySQLdb
from datetime import datetime, timedelta, time, date
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
from bokeh.models import Range1d, Label, BoxAnnotation
from bokeh.palettes import Spectral4 as color
import plot
import sun_info
import os
from dotenv import load_dotenv
from bokeh.io import output_file, show
from bokeh.models import (
  GMapPlot, GMapOptions, ColumnDataSource, Circle, DataRange1d, PanTool, WheelZoomTool, BoxSelectTool
)

app = Flask(__name__)
Mobility(app)
bootstrap = Bootstrap(app)

APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

HOST = os.getenv('HOST')
USR = os.getenv('USR')
PASS = os.getenv('PASS')
DB = os.getenv('DB')


def data():
    sql = """SELECT
                DateTime,
                Temperature,
                WindChill,
                Pressure,
                Humidity,
                WindSpeed,
                WindGusts
            FROM Meteo
            WHERE DateTime > DATE(NOW()) - INTERVAL (7 + WEEKDAY(NOW())) DAY"""
    con = MySQLdb.connect(HOST,USR,PASS,DB)
    df = pd.read_sql(sql, con, index_col='DateTime')
    con.close()
    return df
def pollution_data():
    sql = """SELECT
                date_time,
                location,
                type,
                value
            FROM Pollution
            # WHERE date_time > DATE(NOW()) - INTERVAL (7 + WEEKDAY(NOW())) DAY
            """
    con = MySQLdb.connect(HOST,USR,PASS,DB)
    # df = pd.read_sql(sql, con, index_col='date_time')
    df = pd.read_sql(sql, con)
    df = df.set_index(['date_time','location','type']).unstack(['location','type'])
    con.close()
    return df
def plot_properties():
    dt = datetime.strptime(datetime.strftime(datetime.today(), "%Y-%m-%d 00:00"), "%Y-%m-%d %H:%M")
    if not request.MOBILE:
        mobile = False
        plot_width = 800
        plot_height = 350
        tools = ['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset']
        plot_start = dt - timedelta(days=dt.weekday())
        plot_end = plot_start + timedelta(days=7)
    else:
        mobile = True
        plot_width = 300
        plot_height = 200
        tools = ['pan','box_zoom','reset']
        plot_start = dt - timedelta(days=0)
        plot_end = dt + timedelta(days=1)
    return mobile, plot_width, plot_height, tools, plot_start, plot_end
def get_data_diff(data, df1, df2):
    curr_data = df1[data][-1]
    prev_data = df2[data][df2.index == df1.index[-1]][-1]
    data_diff = curr_data - prev_data
    return curr_data, data_diff
def x_constrain_data_day(df):
    
    df1 = df[df.index >= datetime.combine(date.today(), time()) - timedelta(0)]
    df1 = df1[df1.index < datetime.combine(date.today(), time()) + timedelta(1)]
    df2 = df[df.index >= datetime.combine(date.today(), time()) - timedelta(1)]
    df2 = df2[df2.index < datetime.combine(date.today(), time()) - timedelta(0)]
    df2.index = [x + timedelta(1) for x in df2.index]
    
    return df1, df2
def x_constrain_data_week(df):
    
    df1 = df[df.index >= datetime.combine(date.today(), time()) - timedelta(datetime.today().weekday())]
    df1 = df1[df1.index < datetime.combine(date.today(), time()) + timedelta(1)]
    df2 = df[df.index >= datetime.combine(date.today(), time()) - timedelta(datetime.today().weekday() + 7)]
    df2 = df2[df2.index < datetime.combine(date.today(), time()) - timedelta(datetime.today().weekday())]
    df2.index = [x + timedelta(7) for x in df2.index]
    
    return df1, df2

@app.route('/')
def index():

    df = data()
    df_hr = df.groupby([datetime.strptime(datetime.strftime(x, "%Y-%m-%d %H:00"), "%Y-%m-%d %H:00") for x in df.index]).mean()
    df_hr_wind = df.groupby([datetime.strptime(\
        datetime.strftime(x, "%Y-%m-%d") + ' ' + str(int(datetime.strftime(x, "%H")) - int(datetime.strftime(x, "%H")) % 2) + ':00' \
        , "%Y-%m-%d %H:00") for x in df.index]).mean()
    dt = datetime.strptime(datetime.strftime(datetime.today(), "%Y-%m-%d 00:00"), "%Y-%m-%d %H:%M")
    plot_start = dt - timedelta(days=dt.weekday())
    plot_end = plot_start + timedelta(days=7)
    # df_hr_2 = df_hr[df_hr.index >= plot_start - timedelta(days=7)]
    # df_hr_2 = df_hr[df_hr.index >= plot_start]
    df_hr_2 = df_hr[df_hr.index >= datetime.today() - timedelta(days=7)]

    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()

    #Temperature
    # temp = figure(title='Temperature [\xb0C]' + ' / Current: ' + str(round(df.Temperature[-1],1)), plot_width=plot_width, plot_height=plot_height, x_axis_type="datetime", tools=['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'])
    temp = figure(title='Temperature [C]' + ' / Current: ' + str(round(df.Temperature[-1],1)), plot_width=plot_width, plot_height=plot_height, x_axis_type="datetime", tools=['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'])
    temp.diamond(df_hr.index, df_hr.WindChill, size=4)
    temp.line(df.index, df.Temperature, line_width=1.5, color='red')
    temp.x_range = Range1d(plot_start, plot_end)
    temp.y_range = Range1d(df_hr_2.Temperature.min()-1, df_hr_2.Temperature.max()+1)
    temp.toolbar.logo=None
    temp.toolbar_location=("above" if request.MOBILE == False else None)
    low_box = BoxAnnotation(top=10, fill_alpha=0.1, fill_color='blue')
    mid_box = BoxAnnotation(bottom=10, top=20, fill_alpha=0.1, fill_color='green')
    high_box = BoxAnnotation(bottom=20, fill_alpha=0.1, fill_color='red')
    temp.add_layout(low_box)
    temp.add_layout(mid_box)
    temp.add_layout(high_box)
    # temp_script, temp_div = unicode(components(temp), errors='ignore')
    temp_script, temp_div = components(temp)
    # temp_script, temp_div = components(temp, wrap_plot_info = False)
    
    #Wind Speed
    wind = figure(title="Wind Speed [m/s]" + ' / Current: ' + str(round(df_hr_wind.WindSpeed[-1],1)), plot_width=plot_width, plot_height=plot_height, x_axis_type="datetime", tools=['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'])
    wind.line(df_hr_wind.index, df_hr_wind.WindSpeed, line_width=1.5, color='green')
    wind.diamond(df_hr_wind.index, df_hr_wind.WindGusts, size=2)
    wind.x_range = Range1d(plot_start, plot_end)
    wind.y_range = Range1d(df_hr_2.WindSpeed.min(), df_hr_2.WindSpeed.max())
    wind.toolbar.logo=None
    wind.toolbar_location=("above" if request.MOBILE == False else None)
    wind_script, wind_div = components(wind)
    # wind_script, wind_div = components(wind, wrap_plot_info = False)
    
    #Pressure
    pres = figure(title="Pressure [hPa]" + ' / Current: ' + str(int(df_hr.Pressure[-1])), plot_width=plot_width, plot_height=plot_height, x_axis_type="datetime", tools=['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'])
    pres.line(df_hr.index, df_hr.Pressure, line_width=1.5, color='green')
    pres.x_range = Range1d(plot_start, plot_end)
    pres.y_range = Range1d(df_hr_2.Pressure.min(), df_hr_2.Pressure.max())
    pres.toolbar.logo=None
    pres.toolbar_location=("above" if request.MOBILE == False else None)
    pres_script, pres_div = components(pres)
    # pres_script, pres_div = components(pres, wrap_plot_info = False)
    
    #Humidity
    hum = figure(title="Humidity [%]" + ' / Current: ' + str(int(df_hr.Humidity[-1])), plot_width=plot_width, plot_height=plot_height, x_axis_type="datetime", tools=['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'])
    hum.line(df_hr.index, df_hr.Humidity, line_width=1.5, color='blue')
    hum.x_range = Range1d(plot_start, plot_end)
    # hum.y_range = Range1d(df_hr_2.Humidity.min(), df_hr_2.Humidity.max())
    hum.y_range = Range1d(49, 101)
    hum.toolbar.logo=None
    hum.toolbar_location=("above" if request.MOBILE == False else None)
    hum_script, hum_div = components(hum)
    # hum_script, hum_div = components(hum, wrap_plot_info = False)


    return render_template('bokeh_index.html', script_1=temp_script, div_1=temp_div, script_2=pres_script, div_2=pres_div, script_3=hum_script, div_3=hum_div, script_4=wind_script, div_4=wind_div)
    
@app.route('/air_pollution')
def air_pollution():
    df = pollution_data()
    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()

    #PM25 plot
    script_pm25, div_pm25 = plot.plot_pollution(
        df = df,
        mobile = mobile,
        title = 'PM2.5 Warsaw',
        plot_width = plot_width,
        plot_height = plot_height,
        tools = tools,
        pollution_type = 'PM25',
        locations = ['Ursynow','Marszalkowska','Niepodleglosci'],
        colors = ['red','blue','green'],
        plot_start = plot_start,
        plot_end = plot_end,
        ranges = [0, 12, 36, 60, 84, 120, 1000]
        )
    # PM10 plot
    script_pm10, div_pm10 = plot.plot_pollution(
        df = df,
        mobile = mobile,
        title = 'PM10 Warsaw',
        plot_width = plot_width,
        plot_height = plot_height,
        tools = tools,
        pollution_type = 'PM10',
        locations = ['Ursynow','Marszalkowska','Niepodleglosci'],
        colors = ['red','blue','green'],
        plot_start = plot_start,
        plot_end = plot_end,
        ranges = [0, 20, 60, 100, 140, 200, 1000]
        )
    #PM25 other
    script_pm25_oth, div_pm25_oth = plot.plot_pollution(
        df = df,
        mobile = mobile,
        title = 'PM2.5 Other',
        plot_width = plot_width,
        plot_height = plot_height,
        tools = tools,
        pollution_type = 'PM25',
        locations = ['Otwock','Konstancin','Siedlce'],
        colors = ['red','blue','green'],
        plot_start = plot_start,
        plot_end = plot_end,
        ranges = [0, 12, 36, 60, 84, 120, 1000]
        )
    # PM10 other
    script_pm10_oth, div_pm10_oth = plot.plot_pollution(
        df = df,
        mobile = mobile,
        title = 'PM10 Other',
        plot_width = plot_width,
        plot_height = plot_height,
        tools = tools,
        pollution_type = 'PM10',
        locations = ['Otwock','Konstancin','Siedlce'],
        colors = ['red','blue','green'],
        plot_start = plot_start,
        plot_end = plot_end,
        ranges = [0, 20, 60, 100, 140, 200, 1000]
        )
    return render_template('bokeh_index.html', script_1=script_pm25, div_1=div_pm25, script_2=script_pm10, div_2=div_pm10, script_3=script_pm25_oth, div_3=div_pm25_oth, script_4=script_pm10_oth, div_4=div_pm10_oth)
    
@app.route('/day_to_day')
def day_to_day():

    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()
    
    #get sunrise and sunset time
    sunrise, sunset = sun_info.get_sun_info('day')

    df = data()
    df_agg = df.groupby(pd.TimeGrouper(freq='30Min')).mean()

    df1, df2 = x_constrain_data_day(df)
    df1_agg, df2_agg = x_constrain_data_day(df_agg)

    #Temperature
    curr_temp, temp_diff = get_data_diff('Temperature', df1, df2)
    temp_script, temp_div = plot.plot_comp(
        #general
            # title = 'Temperature [\xb0C]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_temp, 1)), '' if temp_diff < 0 else '+', str(round(temp_diff, 1))),
            title = 'Temperature [C]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_temp, 1)), '' if temp_diff < 0 else '+', str(round(temp_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 5,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Temperature,
            color_1 = 'red',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Temperature,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #Pressure
    curr_pres, pres_diff = get_data_diff('Pressure', df1, df2)
    pres_script, pres_div = plot.plot_comp(
        #general
            title = 'Pressure [hPa]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_pres, 1)), '' if pres_diff < 0 else '+', str(round(pres_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 5,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Pressure,
            color_1 = 'green',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Pressure,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #Humidity
    curr_hum, hum_diff = get_data_diff('Humidity', df1, df2)
    hum_script, hum_div = plot.plot_comp(
        #general
            title = 'Humidity [%]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_hum, 1)), '' if hum_diff < 0 else '+', str(round(hum_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 10,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Humidity,
            color_1 = 'blue',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Humidity,
            color_2 = 'green',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #WindSpeed
    curr_wind, wind_diff = get_data_diff('WindSpeed', df1_agg, df2_agg)
    wind_script, wind_div = plot.plot_comp(
        #general
            title = 'Wind Speed [m/s]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_wind, 1)), '' if wind_diff < 0 else '+', str(round(wind_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2_agg.index.max(),
            xmin = df2_agg.index.min(),
            #ytick_interval = 1,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2_agg.index,
            d1_data = df1_agg.WindSpeed,
            color_1 = 'green',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2_agg.index,
            d2_data = df2_agg.WindSpeed,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    
    return render_template('bokeh_index.html', script_1=temp_script, div_1=temp_div, script_2=pres_script, div_2=pres_div, script_3=hum_script, div_3=hum_div, script_4=wind_script, div_4=wind_div)
    
@app.route('/week_to_week')
def week_to_week():
    
    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()

    #get sunrise and sunset time
    sunrise, sunset = sun_info.get_sun_info('week')

    df = data()
    df_agg = df.groupby(pd.TimeGrouper(freq='1H')).mean()
    
    df1, df2 = x_constrain_data_week(df_agg)


    #Temperature
    curr_temp, temp_diff = get_data_diff('Temperature', df1, df2)
    temp_script, temp_div = plot.plot_comp(
        #general
            # title = 'Temperature [\xb0C]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_temp, 1)), '' if temp_diff < 0 else '+', str(round(temp_diff, 1))),
            title = 'Temperature [C]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_temp, 1)), '' if temp_diff < 0 else '+', str(round(temp_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 5,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Temperature,
            color_1 = 'red',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Temperature,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #Pressure
    curr_pres, pres_diff = get_data_diff('Pressure', df1, df2)
    pres_script, pres_div = plot.plot_comp(
        #general
            title = 'Pressure [hPa]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_pres, 1)), '' if pres_diff < 0 else '+', str(round(pres_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 10,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Pressure,
            color_1 = 'green',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Pressure,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #Humidity
    curr_hum, hum_diff = get_data_diff('Humidity', df1, df2)
    hum_script, hum_div = plot.plot_comp(
        #general
            title = 'Humidity [%]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_hum, 1)), '' if hum_diff < 0 else '+', str(round(hum_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 5,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.Humidity,
            color_1 = 'blue',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.Humidity,
            color_2 = 'green',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )

    #WindSpeed
    curr_wind, wind_diff = get_data_diff('WindSpeed', df1, df2)
    wind_script, wind_div = plot.plot_comp(
        #general
            title = 'Wind Speed [m/s]  /  Current: {}  /  Diff: {}{}'.format(str(round(curr_wind, 1)), '' if wind_diff < 0 else '+', str(round(wind_diff, 1))),
            plot_width = plot_width,
            plot_height = plot_height,
            x_axis_type = 'datetime',
            x_axis_format = DatetimeTickFormatter(minsec = ['%H:%M']),
            xmax = df2.index.max(),
            xmin = df2.index.min(),
            #ytick_interval = 1,
            sunrise = sunrise,
            sunset = sunset,
        #plot1
            type_1 = 'line',
            d1_index = df2.index,
            d1_data = df1.WindSpeed,
            color_1 = 'green',
            line_1_width = 1.5,
            line_1_type = 'solid',
        #plot2
            type_2 = 'line',
            d2_index = df2.index,
            d2_data = df2.WindSpeed,
            color_2 = 'blue',
            line_2_width = 1.5,
            line_2_type = 'dotted'
            )


    return render_template('bokeh_index.html', script_1=temp_script, div_1=temp_div, script_2=pres_script, div_2=pres_div, script_3=hum_script, div_3=hum_div, script_4=wind_script, div_4=wind_div)

@app.route('/day')
def daily():
    
    df = data()
    df_day = df.groupby([datetime.strptime(datetime.strftime(x, "%Y-%m-%d"), "%Y-%m-%d") for x in df.index]).mean()
    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()

    #Temperature
    # temp = figure(title="Temperature [\xb0C]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    temp = figure(title="Temperature [C]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    temp.vbar(bottom=df_day.Temperature.min() - df_day.Temperature.min() % 2, top=df_day.Temperature, x=df_day.index, width=50000000, color='red', alpha=0.75)
    temp.toolbar.logo=None
    temp.toolbar_location = ("above" if request.MOBILE == False else None)
    temp_script, temp_div = components(temp)
    
	#Pressure
    pres = figure(title="Pressure [hPa]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    pres.vbar(bottom=df_day.Pressure.min() - df_day.Pressure.min() % 5, top=df_day.Pressure, x=df_day.index, width=50000000, color='green')
    pres.toolbar.logo=None
    pres.toolbar_location = ("above" if request.MOBILE == False else None)
    pres_script, pres_div = components(pres)
    
    #Humidity
    hum = figure(title="Humidity [%]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    hum.vbar(bottom=df_day.Humidity.min() - df_day.Humidity.min() % 5, top=df_day.Humidity, x=df_day.index, width=50000000, color='blue')
    hum.toolbar.logo=None
    hum.toolbar_location = ("above" if request.MOBILE == False else None)
    hum_script, hum_div = components(hum)
    
    #WindSpeed
    wind = figure(title="WindSpeed [m/s]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    wind.vbar(bottom=0, top=df_day.WindSpeed, x=df_day.index, width=50000000, color='green')
    wind.toolbar.logo=None
    wind.toolbar_location = ("above" if request.MOBILE == False else None)
    wind_script, wind_div = components(wind)
    
    return render_template('bokeh_index.html', script_1=temp_script, div_1=temp_div, script_2=pres_script, div_2=pres_div, script_3=hum_script, div_3=hum_div, script_4=wind_script, div_4=wind_div)

@app.route('/month')
def monthly():
    
    df = data()
    df_day = df.groupby([datetime.strptime(datetime.strftime(x, "%Y-%m"), "%Y-%m") for x in df.index]).mean()
    mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()

    #Temperature
    # temp = figure(title="Temperature [\xb0C]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    temp = figure(title="Temperature [C]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    temp.vbar(bottom=df_day.Temperature.min() - df_day.Temperature.min() % 2, top=df_day.Temperature, x=df_day.index, width=30*50000000, color='red', alpha=0.75)
    temp.toolbar.logo=None
    temp.toolbar_location=("above" if request.MOBILE == False else None)
    temp_script, temp_div = components(temp)
    
    #Pressure
    pres = figure(title="Pressure [hPa]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    pres.vbar(bottom=df_day.Pressure.min() - df_day.Pressure.min() % 5, top=df_day.Pressure, x=df_day.index, width=30*50000000, color='green')
    pres.toolbar.logo=None
    pres.toolbar_location=("above" if request.MOBILE == False else None)
    pres_script, pres_div = components(pres)
    
    #Humidity
    hum = figure(title="Humidity [%]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    hum.vbar(bottom=df_day.Humidity.min() - df_day.Humidity.min() % 5, top=df_day.Humidity, x=df_day.index, width=30*50000000, color='blue')
    hum.toolbar.logo=None
    hum.toolbar_location=("above" if request.MOBILE == False else None)
    hum_script, hum_div = components(hum)
    
    #WindSpeed
    wind = figure(title="WindSpeed [m/s]", plot_width=plot_width, plot_height=250, x_axis_type="datetime")
    wind.vbar(bottom=0, top=df_day.WindSpeed, x=df_day.index, width=30*50000000, color='green')
    wind.toolbar.logo=None
    wind.toolbar_location=("above" if request.MOBILE == False else None)
    wind_script, wind_div = components(wind)
    
    return render_template('bokeh_index.html', script_1=temp_script, div_1=temp_div, script_2=pres_script, div_2=pres_div, script_3=hum_script, div_3=hum_div, script_4=wind_script, div_4=wind_div)

@app.route('/contact')
def contact():
    return render_template('bokeh_index.html', content='kdoju83@gmail.com')

@app.route('/map')
def map():
    # mobile, plot_width, plot_height, tools, plot_start, plot_end = plot_properties()
    map_options = GMapOptions(lat=52.218, lng=21.00, map_type="roadmap", zoom=10)

    locations = ['Ursynow','Marszalkowska','Niepodleglosci','Konstancin','Otwock','Siedlce']
    ranges = [0, 12, 36, 60, 84, 120, 1000]
    colors = ['','green','lightgreen','yellow','orange','orangered','red']
    df = pollution_data()
    col = []
    for location in locations:
        for i in range(1,6):
            val = df['value'][location]['PM25'][-i]
            if val > 0:
                break
        for range_, color in zip(ranges, colors):
            if val <= range_:
                col.append(color)
                break
            

    plot = GMapPlot(
        x_range=DataRange1d(), y_range=DataRange1d(), map_options=map_options
    )
    plot.title.text = "PM2.5"
    plot.api_key = "AIzaSyC_6hfjfDEwgT1tU5NnPJI-g6LzhwjsDHY"

    source = ColumnDataSource(
        data=dict(
            loc=locations,
            col=col,
            lat=[52.1608, 52.2251, 52.219298, 52.082817, 52.115725, 52.172145],
            lon=[21.0338, 21.0148, 21.004724, 21.111121, 21.237297, 22.282001],
        )
    )
    
    circle = Circle(x="lon", y="lat", size=15, fill_color="col", fill_alpha=0.8, line_color='black', line_alpha=0.5)
    plot.add_glyph(source, circle)

    plot.add_tools(PanTool(), WheelZoomTool())

    plot_script, plot_div = components(plot)

    return render_template('bokeh_index.html', script_1=plot_script, div_1=plot_div, script_2='', div_2='', script_3='', div_3='', script_4='', div_4='')


if __name__ == '__main__':
    app.run()
