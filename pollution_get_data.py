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

sensor_ids = [3731, 3730, 16287, 3694, 3585, 3584, 3528, 3526, 16044, 17225, 17240, 17239]
locations = ['Ursynow', 'Ursynow','Marszalkowska','Marszalkowska','Niepodleglosci','Niepodleglosci','Siedlce','Siedlce', 'Otwock', 'Otwock','Konstancin','Konstancin']
types = ['PM25','PM10','PM25','PM10','PM25','PM10','PM25','PM10', 'PM25','PM10','PM25','PM10']

df = pd.DataFrame()

for sensor_id, location, pol_type in zip(sensor_ids, locations, types):
    raw_data = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/' + str(sensor_id))
    json_data = json.loads(raw_data.text)
    df_current = pd.DataFrame(json_data['values'])
    df_current = df_current[:records]
    df_current['location'] = location
    df_current['type'] = pol_type
    df_current = df_current[::-1]
    df = pd.concat([df, df_current], axis=0)

df = df.round(2)

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
