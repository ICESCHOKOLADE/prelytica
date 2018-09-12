# -*- coding: utf-8 -*-
########################
###
### author:     Stefan Rieder
### init_date:     09.08.2018
### topic:         fetch data from meteomatics
###
#######################


import requests
import datetime, json
from helper import *
import psycopg2
import psycopg2.extras
# from base import debug

debug = True

try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
except:
    print "I am unable to connect to the database"
# cur = conn.cursor()
cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)



def meteomatics_cached(plant):
    query = """SELECT data FROM cache_meteomatics WHERE lat = %s AND lon = %s """%(plant.lat, plant.lon)
    # print query
    cur.execute(query)
    data_cached = cur.fetchone()    
    if data_cached:
        return json.loads(data_cached["data"])
    else:
        return False


def set_meteomatics_cache(plant, data):
    query = """ INSERT INTO cache_meteomatics (data, lat, lon)
                VALUES ('%s', %s, %s)
                 """%(json.dumps(data), plant.lat, plant.lon)
    # print query
    cur.execute(query)        
    conn.commit()


def get_data_from_meteomatics(plant):
    auth = get_auth_data("meteomatics")

    if meteomatics_cached(plant):
        return meteomatics_cached(plant)

    url = "http://api.meteomatics.com/2017-04-01T13:00:00ZP10D:PT1H/global_rad:W/%s,%s/html "%(plant.lat, plant.lon)
    # print url

    response = requests.get(url, auth=(auth["username"], auth["password"]))
    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            set_meteomatics_cache(plant, data)
            return data
        except Exception as e:
            raise e
    else:
        print "meteomatics error:", response.status_code
        return False

