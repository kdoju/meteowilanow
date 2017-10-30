import requests
from datetime import datetime, timedelta
import time


def get_sun_info(intvl):
    url = 'https://api.sunrise-sunset.org/json?lat=52.23&lng=21.01'
    r = requests.get(url, stream=True)
    # r = requests.head(url, allow_redirects=False)
    
    year = datetime.today().year
    month = datetime.today().month
    day = datetime.today().day
    weekday = datetime.today().weekday()
    
    sunrise = r.json()['results']['sunrise']
    sunset = r.json()['results']['sunset']
    sunrise = datetime.strptime(sunrise, '%I:%M:%S %p')
    sunset = datetime.strptime(sunset, '%I:%M:%S %p')
    
    sunrise_lst = []
    sunset_lst = []

    if intvl == 'day':
        sunrise_lst.append(time.mktime(datetime(year, month, day, sunrise.hour+2, sunrise.minute, sunrise.second).timetuple())*1000)
        sunset_lst.append(time.mktime(datetime(year, month, day, sunset.hour+2, sunset.minute, sunset.second).timetuple())*1000)
    elif intvl == 'week':
        for i in range(7):
            date = datetime.today() + timedelta(i - weekday)
            year = date.year
            month = date.month
            day = date.day
            sunrise_lst.append(time.mktime(datetime(year, month, day, sunrise.hour + 2, sunrise.minute, sunrise.second).timetuple())*1000)
            sunset_lst.append(time.mktime(datetime(year, month, day, sunset.hour + 2, sunset.minute, sunset.second).timetuple())*1000)
        
    sunrise = sunrise_lst
    sunset = sunset_lst
    
    # sunrise = time.mktime(datetime(year, month, day, 6, 30, 0).timetuple())*1000
    # sunset = time.mktime(datetime(year, month, day, 20, 30, 0).timetuple())*1000
    
    return sunrise, sunset
