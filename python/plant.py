# -*- coding: utf-8 -*-
########################
###
### author:        Stefan Rieder
### init_date:     09.04.2018
### topic:         get all plant details
###
#######################

import csv



debug = True

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
        self.roofparts = {1: {"tilt":30,"aspect":0}, 2:{"tilt":0,"aspect":6}}
        self.ernergy_consumption = 4000
        # load profile is normalized to 1000, so multiply with ernergy_consumption/1000
        self.load_profile = self.get_load_profile()
        self.global_rad = 1166.2
        self.plant_area = 28
        self.wirkungsgrad = 0.14
        print "need to get tetraeder data"

    def get_yearly_plant_yield(self):
        return self.global_rad * self.wirkungsgrad * self.plant_area

    def get_load_profile(self):
        load_profile = {}
        for m in range(1,13):
            load_profile[m] = {}
        with open('../data/load_profiles/pvsol_g4.csv', mode='r') as infile:
            reader = csv.reader(infile, delimiter=';')
            # This skips the first row of the CSV file.
            next(reader)        
            for rows in reader:
                if int(rows[1]) == 27:
                    m = (int(rows[2]))
                    # load profile is normalized to 1000
                    load_profile[m][int(rows[3])] = float(rows[4]) * (self.ernergy_consumption / 1000)
            if debug: print "debug: es wird immer nur der 15. eines Monats genommen. Wochentag / Wochenende"
        # print load_profile["12"]
        return load_profile