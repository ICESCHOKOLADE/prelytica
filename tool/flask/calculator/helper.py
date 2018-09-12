# -*- coding: utf-8 -*-

########################
###
### author: 	Stefan Rieder
### init_date: 	09.02.2018
### topic: 		small helper functions
###
#######################

import calendar
import psycopg2,psycopg2.extras

try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
except:
    print "I am unable to connect to the database"
# cur = conn.cursor()
cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)



def get_monthly_day_count(year, month):
    coun = calendar.monthrange(int(year), int(month))[1]
    return int(coun)


def get_auth_data(service):
    query = """SELECT username, password FROM authentifications WHERE service = '%s' """%(service)
    # print query
    cur.execute(query)
    auth = cur.fetchone()   
    return auth