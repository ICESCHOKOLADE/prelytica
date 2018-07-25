# -*- coding: utf-8 -*-
########################
###
### author:        Stefan Rieder
### init_date:     09.04.2018
### topic:         get all plant details
###
#######################

import csv, math
from external_api_tetraeder import *
from external_api_pvgis import PVGIS_DATA


debug = True

class PLANT(object):
    """docstring for LOCATION"""
    def __init__(self, building_data, roof):
        super(PLANT, self).__init__()
        # plant could be scaffolded, so take newly set plant angles
        self.tilt = roof["plant_tilt"]
        self.aspect = roof["plant_aspect"]
        self.roof_tilt = roof["tilt"]
        self.roof_aspect = roof["aspect"]        
        self.roof_area = roof["area"]
        self.analysed_global_rad = roof["radiation"]
        self.plant_area = 100
        if "plant_kwp" in building_data.args and int(building_data.args["plant_kwp"]) > 0:
            self.plant_kwp = float(building_data.args["plant_kwp"]) # this is rounded, must not fit to panel wp, so recalculate
        else:
            self.plant_kwp = building_data.energy_consumption / 1000
        self.number_of_panels = math.floor(self.plant_kwp * 1000 / building_data.module_wp)
        self.plant_kwp = self.number_of_panels * building_data.module_wp / 1000
        self.plant_area = self.number_of_panels * building_data.module_size
        self.gesamtwirkungsgrad = building_data.gesamtwirkungsgrad
        self.pvgis_data = PVGIS_DATA(building_data.lat, building_data.lon, self.tilt, self.aspect, self.gesamtwirkungsgrad)
        self.pvgis_data_roof = PVGIS_DATA(building_data.lat, building_data.lon, self.roof_tilt, self.roof_aspect, self.gesamtwirkungsgrad)
        self.pvgis_yearly_roof_radiation = self.pvgis_data_roof.yearly_radiation_tilt
        self.pvgis_yearly_radiation_tilt = self.pvgis_data.yearly_radiation_tilt
        del self.pvgis_data_roof

        self.yearly_plant_yield = self.get_yearly_plant_yield()

    def get_yearly_plant_yield(self):
        # faktor dachstrahlung tetraeder und pvgis gleicher winkel (Dach!)
        # korrekturfaktor verrechnen mit aufstaenderung
        self.corr_factor = self.pvgis_yearly_roof_radiation / self.analysed_global_rad
        yearly_yield = self.pvgis_yearly_radiation_tilt / self.corr_factor * self.gesamtwirkungsgrad * self.plant_area
        return yearly_yield

