# -*- coding: utf-8 -*-

########################
###
### author:     Stefan Rieder
### init_date:     09.02.2018
### topic:         handle basic actions
###
#######################



####################
###
###		To Do: Einspeisung & Einsparung auf historische Daten berechnen (jeden Tag)
###
####################


from external_api_pvgis import PVGIS_DATA
from plant_optimizer import OPTIMIZER
from plant import PLANT
from building import BUILDING
from historic_data import HISTORIC_DATA
from helper import *
import psycopg2
import csv, copy
from sys import getsizeof


try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
except:
    print "I am unable to connect to the database"
cur = conn.cursor()


debug = True


class Master(object):
    def __init__(self, lat, lon, args):
        super(Master, self).__init__()
        self.lat = lat
        self.lon = lon
        self.args = args
        self.building_data = BUILDING(lat, lon, args)
        # self.building_data.load_profile_code = "g4"
        # self.building_data.load_profile = self.building_data.get_load_profile()
        self.historic_data = HISTORIC_DATA(self.building_data)
        self.rooflist = {}

        i=1
        for roof in self.building_data.roofs:
            self.rooflist[i] = PLANT(self.building_data, roof)
            self.combine_rad_plant_data(self.rooflist[i])
            self.combine_load_rad_data()
            self.calc_historic_plant_data(self.rooflist[i])
            self.building_data.total_plant_area += self.rooflist[i].plant_area
            self.building_data.total_plant_kwp += self.rooflist[i].plant_kwp
            i+=1
        print "ERROR: total plant size area and kwp are not correct! need to set a target kwp", self.building_data.total_plant_area,self.building_data.total_plant_kwp


        # look for optimum tilt and aspect, keeping roof data in mind. Except flat roofs, you could do anything with them
        # self.best_plant = OPTIMIZER()

    def combine_rad_plant_data(self, roof):
        self.kwh_yield = copy.deepcopy(roof.pvgis_data.global_climate_percentage)
        # now recalculate PVGIS percentage values with global raidation of maybe shadowed roof radiation
        for m in self.kwh_yield["month"]:
            self.kwh_yield["month"][m] *= roof.yearly_plant_yield
            for hour in range(0,24):
                if hour not in self.kwh_yield["hour"][m]:
                    self.kwh_yield["hour"][m][hour] = 0
            for h in self.kwh_yield["hour"][m]:
                # roof.gesamtwirkungsgrad = 1
                # roof.plant_area = 1
                # this is correct, hourly PVGIS data has to be divided by 4 (quarter hours) to get comparable results
                # Also keep gesamtwirkungsgrad and area to 1, to get PVGIS data
                self.kwh_yield["hour"][m][h] *= roof.yearly_plant_yield
            # this is a test print to compare it to PVGIS (check remarks above)
            # if m == "1":
                # print ".", self.kwh_yield["month"]["1"]
        self.kwh_yield["year"] = roof.yearly_plant_yield
        # print self.kwh_yield["year"]
        for m in self.kwh_yield["month"]:
            for h in self.kwh_yield["hour"][m]:
                self.kwh_yield["hour"][m][h] = round(self.kwh_yield["hour"][m][h],2)


    def calc_historic_plant_data(self, roof):
        # print "ERROR this comination is not correct, due to different sun positions in several hours. Now assuming only that sunrise is the same at every angle"
        self.kwh_yield["historic"] = copy.deepcopy(self.historic_data.historic_flat)
        self.kwh_yield["historic"].keys()
        for year in self.kwh_yield["historic"]:
            for m in self.kwh_yield["historic"][year]:
                for d in self.kwh_yield["historic"][year][m]:
                    for h in self.kwh_yield["historic"][year][m][d]:
                        self.kwh_yield["historic"][year][m][d][h] /= roof.pvgis_data.tilt_flat_ratio
                        self.kwh_yield["historic"][year][m][d][h] *= roof.plant_area * roof.gesamtwirkungsgrad

    


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
        for m in self.building_data.load_profile:
            self.load_balance[m]={}
            self.kwh_savings["month"][m], self.kwh_feed_in["month"][m] = 0, 0
            self.kwh_savings["hour"][m], self.kwh_feed_in["hour"][m] = {}, {}
            for h in self.building_data.load_profile[m]:
                # print m, h, self.building_data.load_profile[m][h]
                if str(h) in self.kwh_yield["hour"][str(m)]:
                    energy_yield = self.kwh_yield["hour"][str(m)][str(h)]
                else:
                    energy_yield = 0
                self.load_balance[m][h] = round(self.building_data.load_profile[m][h] - energy_yield, 2)
                if self.building_data.load_profile[m][h] >= energy_yield:
                    kwh_saved = energy_yield
                    kwh_fed_in = 0
                else:
                    kwh_saved = self.building_data.load_profile[m][h]
                    kwh_fed_in = energy_yield - self.building_data.load_profile[m][h]
                self.kwh_savings["hour"][m][h] = kwh_saved * get_monthly_day_count(2018, m)
                self.kwh_savings["month"][m] += kwh_saved * get_monthly_day_count(2018, m)
                self.kwh_savings["year"] += kwh_saved * get_monthly_day_count(2018, m)
                self.kwh_feed_in["hour"][m][h] = kwh_fed_in * get_monthly_day_count(2018, m)
                self.kwh_feed_in["month"][m] += kwh_fed_in * get_monthly_day_count(2018, m)
                self.kwh_feed_in["year"] += kwh_fed_in * get_monthly_day_count(2018, m)   
                self.building_data.load_profile[m][h] = round(self.building_data.load_profile[m][h],2)
                # if m == 5:
                    # print h, self.load_balance[m][h] , self.building_data.load_profile[m][h], energy_yield, kwh_saved, kwh_fed_in     

        # for x in self.kwh_yield:
        #   print self.kwh_yield["year"]
        # print "self.kwh_yield", self.kwh_yield["hour"]["1"]
        # print "self.load_profile", self.building_data.load_profile[1]
        # print "self.load_balance", self.load_balance[1]
        # print "self.kwh_savings", self.kwh_savings["month"][6], self.kwh_savings["year"]
        # print "Ertrag, Verbrauch", self.kwh_yield["year"], self.building_data.energy_consumption
        self.own_consumption = self.kwh_savings["year"] / self.kwh_yield["year"]
        self.autarky = self.kwh_savings["year"] / self.building_data.energy_consumption
        print "autarky:", self.autarky, "eigenverbrauch:", self.own_consumption
        # print "year saved kwh", self.kwh_savings["year"]


    def get_export_data(self):
        data = {
            "kwh_feed_in": self.kwh_feed_in,
            "kwh_savings": self.kwh_savings,
            "autarky": self.autarky,
            "own_consumption": self.own_consumption,
            "kwh_yield": self.kwh_yield,
            "load_profile": self.building_data.load_profile,
            "load_balance": self.load_balance,
            "tetraeder_data": self.building_data.potential_data,
            # "plant_data": self
        }


        return data



lat = 52.402958
lon = 12.506151

args = {
    "load_profile": "g2",
    "energy_consumption": 30000
}


# Master(lat, lon, args)
print "ENDE: bei autarkie und eigenverbrauch. Diese stimmen"
print "NEXT: Zusammenführen mehrerer Dachteilflächen, ein gemeinsamer Autarkiewert"
print "NEXT: Zusammenführen mehrerer Dachteilflächen, ein gemeinsamer Autarkiewert"





cur.close()
conn.close()