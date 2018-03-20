########################
###
### author: 	Stefan Rieder
### init_date: 	09.02.2018
### topic: 		handle basic actions
###
#######################

from external_api_pvgis import PVGIS_DATA
from helper import *
import psycopg2



try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
except:
    print "I am unable to connect to the database"
cur = conn.cursor()



class PLANT(object):
	"""docstring for LOCATION"""
	def __init__(self, lat, lon):
		super(PLANT, self).__init__()
		# self.arg = arg
		self.lat = round(lat,3)
		self.lon = round(lon,3)
		self.tilt = 30
		self.aspect = 0
		self.system_loss = 0.14
		self.module_efficiency = 0.15


lat = 51
lon = 10


plant_data = PLANT(lat, lon)
pvgis_data = PVGIS_DATA(plant_data)



cur.close()
conn.close()