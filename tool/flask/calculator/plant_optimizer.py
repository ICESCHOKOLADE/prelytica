# -*- coding: utf-8 -*-
########################
###
### author:        Stefan Rieder
### init_date:     09.04.2018
### topic:         do plant optimization, find best suited plant to cut power peaks
###
#######################


# import datetime, json
from helper import *
# import psycopg2
# import psycopg2.extras


debug = True

class OPTIMIZER(object):
    def __init__(self, plant_data, pvgis_data):
        super(OPTIMIZER, self).__init__()
        self.plant_data = plant_data
        self.pvgis_data = pvgis_data

        self.analyze_load_profile()

    def analyze_load_profile(self):
    	# print self.plant_data.load_profile
    	pass