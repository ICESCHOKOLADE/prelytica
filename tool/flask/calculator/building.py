# -*- coding: utf-8 -*-
########################
###
### author:        Stefan Rieder
### init_date:     09.04.2018
### topic:         get all plant details
###
#######################

import csv
from external_api_tetraeder import *


debug = True

class BUILDING(object):
    """docstring for LOCATION"""
    def __init__(self, lat, lon, args):
        super(BUILDING, self).__init__()
        self.args = args
        self.lat = round(lat,5)
        self.lon = round(lon,5)
        self.system_loss = 0.14
        self.module_efficiency = 0.15
        self.module_size = 1.635
        self.module_wp = 270
        self.gesamtwirkungsgrad = (1 - 0.20) * self.module_efficiency
        self.energy_consumption = 25000
        self.total_plant_area = 0
        self.total_plant_kwp = 0
        if "energy_consumption" in args:
            self.energy_consumption = int(args["energy_consumption"])
        self.load_profile_code = "g0"
        if "load_profile" in args:
            self.load_profile_code = args["load_profile"]            
        self.load_profile = self.get_load_profile()
        # load profile is normalized to 1000, so multiply with energy_consumption/1000
        self.potential_data = get_data_from_tetraeder(self)
        self.hid = self.potential_data["request"]["hid"]
        print "HID:", self.hid
        # print self.potential_data
        self.roofs = []
        for roof in self.potential_data["results"][0]["roofs"]:
            if roof["area"] < 30:
                # self.roofs.remove(roof)
                continue
            if roof["tilt"] < 10:
                roof["plant_tilt"] = 15
                roof["plant_aspect"] = 90
                if "flat_tilt" in self.args:
                    roof["plant_tilt"] = self.args["flat_tilt"]
                if "flat_aspect" in self.args:
                    roof["plant_aspect"] = self.args["flat_aspect"]                    
            else:
                roof["plant_tilt"] = roof["tilt"]
                roof["plant_aspect"] = roof["aspect"]
            self.roofs.append(roof)

    def get_load_profile(self):
        load_profile = {}
        for m in range(1,13):
            load_profile[m] = {}

        filename = '/home/stefan/prelytica/data/load_profiles/pvsol_%s.csv'%self.load_profile_code
        # print filename
        with open(filename, mode='r') as infile:
            reader = csv.reader(infile, delimiter=';')
            # This skips the first row of the CSV file.
            next(reader)        
            for rows in reader:
                if int(rows[1]) == 15:
                    m = (int(rows[2]))
                    # load profile is normalized to 1000
                    a = rows[4]
                    if "," in a:
                        a = a.replace(",",".")
                    a = float(a)
                    load_profile[m][int(rows[3])] = a * (self.energy_consumption / 1000)
                    # if m == 5:
                    #     print int(rows[3]), a
            if debug: print "debug: es wird immer nur der 15. eines Monats genommen. Wochentag / Wochenende"
        # print load_profile[5]
        return load_profile