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





def build_graph(x_coordinates, y_coordinates, name):
	img = io.BytesIO()
	plt.figure(figsize=(17,3))
	plt.plot(x_coordinates, y_coordinates)
	# plt.set_size_inches(18.5, 10.5)
	plt.savefig(img, format='png')
	plt.savefig('../../../img/%s.png'%name)
	img.seek(0)
	graph_url = base64.b64encode(img.getvalue()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(graph_url)	



		
class PVPLANT(object):
	"""docstring for PVPLANT"""
	def __init__(self):
		super(PVPLANT, self).__init__()
		self.module_wp = 270
		self.module_width = 1.65
		self.module_height = 0.99
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
		self.time = "present"


		if self.time == "present":
			self.start_year = 1970
			self.end_year = 2000
		elif self.time == "future":
			self.start_year = 2070
			self.end_year = 2100
		self.current_year = self.start_year


		# self.tas = self.get_model_data("tas")
		self.rsds = self.get_model_data("rsds")
		# self.pr = self.get_model_data("pr")
		# print len(self.tas), len(self.pr), len(self.rsds)



		self.drought_threshold = 1.0 # in mm per day
		self.drought_duration_threshold = 5 # consecutive days
		# self.droughts = self.get_droughts()


		self.energy_yield = self.simulate_pv_plant()
		self.energy_yield_list = self.convert_energy_yield()

		a = build_graph(self.energy_yield_list["brandenburg"]["years_x"], self.energy_yield_list["brandenburg"]["years_y"], "brandenburg")
		print a



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
		for i in time_series:
			y, m, d, h = i["year"], i["month"], i["day"], i["hour"]/100
			# print y, m, d, h
			if y == y:
				for station in self.stations:
					radiation = float(i[station]) * 3.0 / 1000 # convert units
					energy_yield = radiation * PV_PLANT.efficiency_factor * PV_PLANT.area


					if y not in out[station]["years"]: 
						out[station]["years"][y] = 0
						out[station]["course"][y] = {}
					else:
						out[station]["years"][y] += energy_yield

					if m not in out[station]["course"][y]: 
						out[station]["course"][y][m] = 0
					else:
						out[station]["course"][y][m] += energy_yield			

		# print out["brandenburg"]["course"]
		return out


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


class Station(object):
	"""docstring for Station"""
	def __init__(self, name, arg):
		super(Station, self).__init__()
		self.arg = arg
		self.name = name

print "INIT MODEL, FETCHING DATA"
PVMODEL = PVMODEL()



print "ENDE"
