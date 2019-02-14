# -*- coding: utf-8 -*-
########################
###
### author:     Stefan Rieder
### init_date:  09.02.2019
### topic:      
###
#######################

import sys, io, csv, os, base64
import requests
import datetime, json
import psycopg2
import psycopg2.extras
from db  import *

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

cur = connect_db()
if not cur:
	print "NO DATABASE CONNECTED"








		
class PVPLANT(object):
	"""docstring for PVPLANT"""
	def __init__(self):
		super(PVPLANT, self).__init__()
		self.module_wp = 270
		self.module_width = 1.65
		self.module_height = 0.99
		self.module_temp_koeff = 0.5 # %/K
		self.module_efficiency = self.module_wp / 1000.0 / (self.module_width * self.module_height)

		self.plant_loss = 0.2
		self.efficiency_factor = self.module_efficiency * (1 - self.plant_loss)
		# print self.module_efficiency, self.efficiency_factor

		self.climate_loss = 0 

		self.area = 1 # plant area in square meters



class PVMODEL(object):
	"""docstring for Model"""
	def __init__(self):
		super(PVMODEL, self).__init__()
		self.stations = ["brandenburg", "amsterdam", "minden", "wuerzburg"]
		# self.stations = ["brandenburg"]
		self.scenario = "rcp85"
		self.time = "future"

		self.rad_unit = "kWh/qm"
		# self.rad_unit = "W/qm"

		self._climate_loss = True 

		
		if self.time == "present":
			self.start_year = 1970
			self.end_year = 2000
		elif self.time == "future":
			self.start_year = 2070
			self.end_year = 2100
		self.current_year = self.start_year


		self.label = self.scenario + "_" + str(self.start_year) + "_" + str(self.end_year)


		self.tas = self.get_model_data("tas")
		self.rsds = self.get_model_data("rsds")
		# self.pr = self.get_model_data("pr")
		# print len(self.tas), len(self.pr), len(self.rsds)



		self.drought_threshold = 1.0 # in mm per day
		self.drought_duration_threshold = 5 # consecutive days
		# self.droughts = self.get_droughts()


		self.energy_yield = self.simulate_pv_plant()
		self.energy_yield_list = self.convert_energy_yield()
		self.energy_yield_summary = self.calculate_yield_statistics()

		# print self.energy_yield["wuerzburg"]["years"]


		x = self.energy_yield_list["wuerzburg"]["years_x"]
		y = self.energy_yield_list["wuerzburg"]["years_y"]
		a = self.build_graph("Year", x, "radiation in %s"%self.rad_unit, y, "brandenburg")
		# print a



	def get_model_data(self, parameter):
		query = """SELECT * FROM %s_%s WHERE year >= %s and year <= %s order by id"""%(parameter, self.scenario, self.start_year, self.end_year)
		cur.execute(query)
		data = cur.fetchall()  
		return data

	
	def get_aggregated_model_data(self, parameter):
		if parameter == "pr":
			query = """SELECT year, month, day, sum(wuerzburg) as wuerzburg, sum(brandenburg) as brandenburg,\
						sum(minden) as minden, sum(amsterdam) as amsterdam
						 FROM %s_%s WHERE year >= %s and year <= %s group by year, month, day\
						 order by year, month, day"""%(parameter, self.scenario, self.start_year, self.end_year)
		cur.execute(query)
		data = cur.fetchall()  
		return data



	def convert_energy_yield(self):
		out = {}

		for station in self.energy_yield:
			out[station] = {
				"years_x": [],
				"years_y": [],
				"course_total_y": [],
				"course_total_x": [],
				"course": {},
				}
			for y in self.energy_yield[station]["years"]:
				out[station]["years_x"].append(y)
				out[station]["years_y"].append(round(self.energy_yield[station]["years"][y],2))
			for y in self.energy_yield[station]["course"]:
				if y not in out[station]["course"]:
					out[station]["course"][y] = []
				for m in self.energy_yield[station]["course"][y]:
					out[station]["course_total_x"].append(str(y)+"-"+str(m))
					out[station]["course_total_y"].append(round(self.energy_yield[station]["course"][y][m],2))
					out[station]["course"][y].append(round(self.energy_yield[station]["course"][y][m],2))

		# print out["brandenburg"]["course_total_y"]
		# print out["brandenburg"]["course_total_x"]
		return out


	def simulate_pv_plant(self):
		PV_PLANT = PVPLANT()
		time_series = self.rsds
		out = {}
		for station in self.stations:
			out[station] = {"years":{}, "course":{}}

		self.current_index = 0
		for i in time_series:
			self.current_y, self.current_m, self.current_d, self.current_h = i["year"], i["month"], i["day"], i["hour"]/100
			# print y, m, d, h
			if self.current_y == self.current_y:
				for station in self.stations:
					self.current_station = station
					radiation = float(i[station]) * 3.0 / 1000 # convert units
					# if self.current_y == 2000 and self.current_m== 5:
						# print radiation
					energy_yield = radiation * PV_PLANT.efficiency_factor * PV_PLANT.area
					if self._climate_loss:
						energy_yield *= (1 - self.calc_climate_loss(PV_PLANT))
					if self.rad_unit == "kWh/qm":
						energy_yield = energy_yield / 1000.0 * 8760 # convert from W/qm to kWh/qm

					if self.current_y not in out[station]["years"]: 
						out[station]["years"][self.current_y] = 0
						out[station]["course"][self.current_y] = {}
					else:
						out[station]["years"][self.current_y] += energy_yield

					if self.current_m not in out[station]["course"][self.current_y]: 
						out[station]["course"][self.current_y][self.current_m] = 0
					else:
						out[station]["course"][self.current_y][self.current_m] += energy_yield			
			self.current_index += 1
		# print out["brandenburg"]["course"]
		return out


	def calculate_yield_statistics(self):
		out = {}
		for i in self.energy_yield_list:		
			out[i] = {}
			count, summ = 0, 0
			# print i, self.energy_yield_list["years_y"]
			out[i]["mean"] = sum(self.energy_yield_list[i]["years_y"]) / float(len(self.energy_yield_list[i]["years_y"]))

		print "mean", out
		return out


	def calc_climate_loss(self,PV_PLANT):
		self.climate_loss = 0
		radiation = float(self.rsds[self.current_index][self.current_station])#* 3.0 / 1000
		temperature = float(self.tas[self.current_index][self.current_station])
		# a[str(self.current_y)+"_"+str(self.current_m)"_"+str(self.current_d)]
		i = 25
		j = 6.84 # 6.11
		wind = 0
		module_temp = temperature + (radiation / (i + j * wind))
		loss_temp = (module_temp - 25) * PV_PLANT.module_temp_koeff / 100
		# if self.current_y == 2000 and self.current_m== 7 and self.current_station=="wuerzburg":
			# print self.current_d, self.current_h, radiation, temperature, module_temp
			# print loss_temp
		self.climate_loss = loss_temp
		return self.climate_loss

	def get_droughts(self):
		stations_out = {}
		wrk_dict = {}
		extreme_std = {
			"start": None,
			"end": None,
			"value": None,
			"duration": None
		}

		for station in self.stations:
			stations_out[station] = []
			wrk_dict[station] = extreme_std.copy()

		daily_precipition = self.get_aggregated_model_data("pr")
		for i in daily_precipition:
			y, m, d = i["year"], i["month"], i["day"]

			if m >= 4 and m <= 9:
			# if m == 4 and y == 1990:
				for station in self.stations:
					# print y, m, d, i[station]
					if i[station] < self.drought_threshold:
						if wrk_dict[station]["start"] is None:
							# print "start extreme"
							wrk_dict[station]["start"] = str(y)+"-"+str(m)+"-"+str(d)
							wrk_dict[station]["value"] = i[station]
							wrk_dict[station]["duration"] = 1
						else:
							# print "extend extreme"
							wrk_dict[station]["duration"] += 1
							wrk_dict[station]["value"] += i[station]
							wrk_dict[station]["end"] = str(y)+"-"+str(m)+"-"+str(d)
					else:
						# print "stop extreme"
						if wrk_dict[station]["duration"] and wrk_dict[station]["duration"] > self.drought_duration_threshold:
							# print "append extreme"
							stations_out[station].append(wrk_dict[station])
						# reset, no extreme drought
						wrk_dict[station] = extreme_std.copy()

		for station in stations_out:
			print u"Es gab in %s %s Dürreperioden"%(station, len(stations_out[station]))

		return stations_out





	def build_graph(self, x_name, x_coordinates, y_name, y_coordinates, name):
		img = io.BytesIO()
		plt.figure(figsize=(20,10))
		plt.plot(x_coordinates, y_coordinates)
		# plt.set_size_inches(18.5, 10.5)
		plt.xlabel(x_name)
		plt.ylabel(y_name)
		plt.title('Radiation in %s'%name)
		plt.tight_layout()
		plt.savefig(img, format='png')
		path_root = os.path.dirname(__file__)
		name = name+"_"+self.label
		path = os.path.join(path_root, "../../../img/%s.png"%name)
		path = os.path.abspath(path)
		plt.savefig(path, dpi=200)
		img.seek(0)
		graph_url = base64.b64encode(img.getvalue()).decode()
		plt.close()
		print "  SAVED IMAGE at "+path
		return 'data:image/png;base64,{}'.format(graph_url)	


class Station(object):
	"""docstring for Station"""
	def __init__(self, name, arg):
		super(Station, self).__init__()
		self.arg = arg
		self.name = name

print "INIT MODEL, FETCHING DATA"
PVMODEL = PVMODEL()



print "ENDE"
