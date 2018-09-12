# -*- coding: utf-8 -*-
########################
###
### author:     Stefan Rieder
### init_date:     09.02.2018
### topic:         fetch data from tetraeder
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



def tetraeder_cached(plant):
    query = """SELECT data FROM cache_tetraeder WHERE lat = %s AND lon = %s """%(plant.lat, plant.lon)
    # print query
    cur.execute(query)
    data_cached = cur.fetchone()    
    if data_cached:
        return json.loads(data_cached["data"])
    else:
        return False


def set_tetraeder_cache(plant, data):
    query = """ INSERT INTO cache_tetraeder (data, lat, lon)
                VALUES ('%s', %s, %s)
                 """%(json.dumps(data), plant.lat, plant.lon)
    # print query
    cur.execute(query)        
    conn.commit()




def get_data_from_tetraeder(plant):
    auth = get_auth_data("tetraeder")

    if tetraeder_cached(plant):
        return tetraeder_cached(plant)

    url = "https://detailskronos.solare-stadt.de/hub/api/lat_lon_search/stadt_brandenburg/%s/%s/"%(plant.lat, plant.lon)
    url += "?energy_consumption=%s&rooflist"%(plant.energy_consumption)
    # print url

    response = requests.get(url, auth=(auth["username"], auth["password"]))
    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            set_tetraeder_cache(plant, data)
            return data
        except Exception as e:
            raise e
    else:
        print "tetraeder error:", response.status_code
        return False

