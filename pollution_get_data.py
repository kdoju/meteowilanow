#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
import MySQLdb
from dotenv import load_dotenv
import os

APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

HOST = os.getenv('HOST')
USR = os.getenv('USR')
PASS = os.getenv('PASS')
DB = os.getenv('DB')

count = 0
records = 5

war_urs_pm25 = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/3731')
war_urs_pm10 = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/3730')
war_mar_pm25 = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/16287')
war_mar_pm10 = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/3694')

data_mar_pm25 = json.loads(war_mar_pm25.text)
data_mar_pm10 = json.loads(war_mar_pm10.text)
data_urs_pm25 = json.loads(war_urs_pm25.text)
data_urs_pm10 = json.loads(war_urs_pm10.text)

df_mar_pm25 = pd.DataFrame(data_mar_pm25['values'])
df_mar_pm25 = df_mar_pm25[:records]
df_mar_pm25['location'] = 'Marszalkowska'
df_mar_pm25['type'] = 'PM25'

df_mar_pm10 = pd.DataFrame(data_mar_pm10['values'])
df_mar_pm10 = df_mar_pm10[:records]
df_mar_pm10['location'] = 'Marszalkowska'
df_mar_pm10['type'] = 'PM10'

df_urs_pm25 = pd.DataFrame(data_urs_pm25['values'])
df_urs_pm25 = df_urs_pm25[:records]
df_urs_pm25['location'] = 'Ursynow'
df_urs_pm25['type'] = 'PM25'

df_urs_pm10 = pd.DataFrame(data_urs_pm10['values'])
df_urs_pm10 = df_urs_pm10[:records]
df_urs_pm10['location'] = 'Ursynow'
df_urs_pm10['type'] = 'PM10'

df = pd.concat([df_mar_pm10, df_mar_pm25, df_urs_pm10, df_urs_pm25], axis=0)
df = df.round(2)
# df = df.set_index(['date','location','type'])
df = df[::-1]
# print df

con = MySQLdb.connect(HOST,USR,PASS,DB)
c = con.cursor()

for index, row in df.iterrows():
    if not pd.isnull(row['value']):
        try:
            c.execute("""INSERT INTO Pollution (date_time, location, type, value)
                        VALUES (%s, %s, %s, %s);""", \
                        (row['date'], row['location'], row['type'], row['value']))
            print ("Row inserted successfully: ", row['date'], row['location'], row['type'], row['value'])
            count += 1
        except MySQLdb.IntegrityError:
            # print "IntegrityError: Can't insert record to table: " + row['date'], row['location'], row['type'], row['value']
            pass
    # else:
    #     print "Row not inserted (nan): ", row['date'], row['location'], row['type'], row['value']

con.commit()

print ('Rows inserted: ' + str(count))
