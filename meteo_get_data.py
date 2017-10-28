#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from lxml.html import parse
from urllib import request
from datetime import datetime

parsed = parse(request.urlopen('http://if.pw.edu.pl/~meteo'))
doc = parsed.getroot()

tables = doc.findall('.//table')
rows = tables[1].findall('.//tr')

info = rows[0].findall('.//td')
data = rows[2].findall('.//td')

date_time = info[1].text_content().split('):')[1].strip()
temp = data[0].text_content().strip()[:-3]
temp_wc = data[1].text_content().strip()[:-3]
press = data[2].text_content().strip().strip('hPa').strip()
hum = data[3].text_content().strip().strip('%').strip()

if data[4].text_content().find('w porywach do') > -1:
    search_str = 'w porywach do'
else:
    search_str = 'up to'

wind = data[4].text_content().split(search_str)[0].strip().strip('m/s').strip()
wind_gusts = data[4].text_content().split(search_str)[1].strip().strip('m/s').strip()

if wind.find(',') > -1:
    temp = temp.replace(',', '.')
    temp_wc = temp_wc.replace(',', '.')
    press = press.replace(',', '.')
    wind = wind.replace(',', '.')
    wind_gusts = wind_gusts.replace(',', '.')


insert = [date_time, temp, temp_wc, press, hum, wind, wind_gusts]

con = MySQLdb.connect('localhost','kdoju_meteo','kdoju_meteo','kdoju_meteo')
c = con.cursor()

c.execute("SELECT DateTime FROM Meteo ORDER BY ID DESC LIMIT 1")
row=c.fetchall()
current_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')
if len(row) > 0:
        prev_time = str(row[0][0])
else:
        prev_time = ''

insert = True
if prev_time[:-3] == current_time:
    insert = False
#print prev_time[:-3]
#print current_time
#print insert
if insert == True:
    c.execute("""INSERT INTO Meteo (DateTime, Temperature, WindChill, Pressure, Humidity, WindSpeed, WindGusts) VALUES (%s, %s, %s, %s, %s, %s, %s);""", (date_time, temp, temp_wc, press, hum, wind, wind_gusts))
    con.commit()


