# -*- coding: utf-8 -*-

########################
###
### author:     Stefan Rieder
### init_date:     09.02.2018
### topic:         handle basic actions
###
#######################

from external_api_pvgis import PVGIS_DATA
from plant_optimizer import OPTIMIZER
from plant import PLANT
from helper import *
import psycopg2
import csv, copy



try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
except:
    print "I am unable to connect to the database"
cur = conn.cursor()


debug = True


lat = 50
lon = 10



class Master(object):
    def __init__(self, lat,lon):
        super(Master, self).__init__()
        self.lat = lat
        self.lon = lon
        self.plant_data = PLANT(lat, lon)
        self.pvgis_data = PVGIS_DATA(self.plant_data)

        print "debug: set plant global radiation to pvgis global radiation"
        self.plant_data.global_rad = self.pvgis_data.yearly_radiation

        self.combine_rad_plant_data()
        self.combine_load_rad_data()

        # look for optimum tilt and aspect, keeping roof data in mind. Except flat roofs, you could do anything with them
        # self.best_plant = OPTIMIZER()

    def combine_rad_plant_data(self):
        self.kwh_yield = copy.deepcopy(self.pvgis_data.global_climate_percentage)
        # now recalculate PVGIS percentage values with global raidation of maybe shadowed roof radiation
        for m in self.kwh_yield["month"]:
            self.kwh_yield["month"][m] *= self.plant_data.get_yearly_plant_yield()
            for h in self.kwh_yield["hour"][m]:
            	# self.plant_data.wirkungsgrad = 1
            	# self.plant_data.plant_area = 1
            	# this is correct, hourly PVGIS data has to be divided by 4 (quarter hours) to get comparable results
            	# Also keep wirkungsgrad and area to 1, so get PVGIS data
                self.kwh_yield["hour"][m][h] *= self.plant_data.get_yearly_plant_yield()
            # this is a test print to compare it to PVGIS (check remarks above)
            # if m == "1":
            	# print ".", self.kwh_yield["month"]["1"]
        self.kwh_yield["year"] = self.plant_data.get_yearly_plant_yield()
        # print self.kwh_yield["year"]


    


    def combine_load_rad_data(self):
    	# calculate differences and savings between load profile and energy yield
        self.load_balance = {}
        self.kwh_savings = {
        	"month": {},
        	"hour": {},
        	"year": 0
        }
        self.kwh_feed_in = {
        	"month": {},
        	"hour": {},
        	"year": 0
        }        
        for m in self.plant_data.load_profile:
            self.load_balance[m]={}
            self.kwh_savings["month"][m], self.kwh_feed_in["month"][m] = 0, 0
            self.kwh_savings["hour"][m], self.kwh_feed_in["hour"][m] = {}, {}
            for h in self.plant_data.load_profile[m]:
                # print m, h, self.plant_data.load_profile[m][h]
                if str(h) in self.kwh_yield["hour"][str(m)]:
                    energy_yield = self.kwh_yield["hour"][str(m)][str(h)]
                else:
                    energy_yield = 0
                self.load_balance[m][h] = self.plant_data.load_profile[m][h] - energy_yield
                if self.plant_data.load_profile[m][h] >= energy_yield:
                	kwh_saved = energy_yield
                	kwh_fed_in = 0
                else:
                	kwh_saved = self.plant_data.load_profile[m][h]
                	kwh_fed_in = energy_yield - self.plant_data.load_profile[m][h]
            	self.kwh_savings["hour"][m][h] = kwh_saved * get_monthly_day_count(2018, 5)
            	self.kwh_savings["month"][m] += kwh_saved * get_monthly_day_count(2018, 5)
            	self.kwh_savings["year"] += kwh_saved * get_monthly_day_count(2018, 5)
            	self.kwh_feed_in["hour"][m][h] = kwh_fed_in * get_monthly_day_count(2018, 5)
            	self.kwh_feed_in["month"][m] += kwh_fed_in * get_monthly_day_count(2018, 5)
            	self.kwh_feed_in["year"] += kwh_fed_in * get_monthly_day_count(2018, 5)            	
                # if m == 5:
                	# print h, self.load_balance[m][h] , self.plant_data.load_profile[m][h], energy_yield, kwh_saved, kwh_fed_in 	

        # for x in self.kwh_yield:
        # 	print self.kwh_yield["year"]
        # print "self.kwh_yield", self.kwh_yield["hour"]["1"]
        # print "self.load_profile", self.plant_data.load_profile[1]
        # print "self.load_balance", self.load_balance[1]
        print "self.kwh_savings", self.kwh_savings["month"][1], self.kwh_savings["year"], self.kwh_feed_in["year"]
        print  self.kwh_yield["year"], self.plant_data.ernergy_consumption
        own_consumption = self.kwh_savings["year"] / self.kwh_yield["year"]
        autarky = self.kwh_savings["year"] / self.plant_data.ernergy_consumption
        print "autarky:", autarky, "eigenverbrauch:", own_consumption
        print "ENDE bei autarkie und eigenverbrauch. Diese sollten auch stimmen"




Master(lat,lon)






cur.close()
conn.close()