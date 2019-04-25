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
import numpy as np


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

		self.plant_loss = 0.08 # without temp loss and so on! Just technical losses
		self.efficiency_factor = self.module_efficiency * (1 - self.plant_loss)
		# print self.module_efficiency, self.efficiency_factor

		self.climate_loss = 0 

		self.area = 1 # plant area in square meters



class PVMODEL(object):
	"""docstring for Model"""
	def __init__(self):
		super(PVMODEL, self).__init__()
		self.timesteps_per_day = 8
		self.stations = ["amsterdam", "minden", "brandenburg", "wuerzburg"]
		# self.stations = ["wuerzburg", "brandenburg", "amsterdam"]
		# self.stations = ["minden"]
		self.scenario = "rcp85"
		self.time = "future"
		# self.time = "present"
		times = ["present", "future"]
		# times = ["present"]

		self.rad_unit = "kWh/qm"
		# self.rad_unit = "W/qm"

		self._climate_loss = True 
		self._deposit_loss = True
		self.climate_loss_cfg = {
			"deposit_start": 3, # month
			"deposit_end": 9, #month
			"rain_clean_treshold": 4, # in mm/m² bzw. l/m² per ...
			"rain_clean_interval": 3, # in timesteps
			"deposit_loss_day": 0.01, # per day in percent
		}
		self.climate_loss_cfg["deposit_loss_timestep"] = self.climate_loss_cfg["deposit_loss_day"] / float(self.timesteps_per_day) 
		self.climate_loss_data = {}

		

		for t in times:
			print "INIT MODEL, FETCHING DATA FOR", t
			self.time = t
			self.set_years()
			self.current_year = self.start_year

			self.temporary_data = {}

			self.label = self.scenario + "_" + str(self.start_year) + "_" + str(self.end_year)
			self.time = t
			self.wind = self.get_model_data("wind")
			self.tas = self.get_model_data("tas")
			self.rsds = self.get_model_data("rsds")
			self.pr = self.get_model_data("pr")
			# print len(self.tas), len(self.pr), len(self.rsds)

			# if self._climate_loss == True:
			# 	self.temporary_data["last_dry_period"] = {}
			# 	print 1
			# 	for t in self.pr:
			# 		if int(t["month"]) >= self.climate_loss_cfg["deposit_start"]-1:
			# 			print t

			# 			exit()	
			# 			for station in self.stations:
			# 				# self.temporary_data["last_dry_period"][station] = 1
			# 				a = float(t[station])




			self.drought_threshold = 1.0 # in mm per day
			self.drought_duration_threshold = 5 # consecutive days
			# self.droughts = self.get_droughts()


			self.energy_yield = self.simulate_pv_plant()
			self.energy_yield_list = self.convert_energy_yield()
			self.energy_yield_summary = self.calculate_yield_statistics()

			# print self.energy_yield["wuerzburg"]["years"]
			self.accumulate_climate_loss()
			self.graph_create_monthly_climate_loss()

			self.graph_create_yearly_energy_yield()

		# print self.climate_loss_data
		print "TODO: Graphische Ausgabe der Parameter Temperatur und Strahlung"
		print "TODO: (Graphische) Ausgabe der Zusammensetzung des Verlusts durch Klima (Temp & Ablagerung)"

	def set_years(self):
		if self.time == "present":
			self.start_year = 1970
			self.end_year = 2000
		elif self.time == "future":
			self.start_year = 2070
			self.end_year = 2100		

	def accumulate_climate_loss(self):
		print "ATTENTION: be aware, loss accumulated is mean of all values, even at night, so less amplitudes"
		a = {}
		for station in self.climate_loss_data:
			a[station] = {}
			for y in self.climate_loss_data[station]:
				a[station][y] = {}
				for m in self.climate_loss_data[station][y]:
					a[station][y][m] = sum(self.climate_loss_data[station][y][m]) / float(len(self.climate_loss_data[station][y][m]))
					# print station, y, m, len(self.climate_loss_data[station][y][m]), a[station][y][m]

		b = {}
		for station in a:
			b[station] = {}
			for y in a[station]:
				for m in a[station][y]:
					if m not in b[station]:
						b[station][m] = []
					b[station][m].append(a[station][y][m])

		for station in b:
			b[station]["list"] = []
			for m in b[station]:
				if m == "list": continue
				b[station][m] = round(sum(b[station][m]) / float(len(b[station][m])),6)
				b[station]["list"].append(b[station][m])


		self.climate_loss_accumulated = b


	def graph_create_monthly_climate_loss(self):
		name = "Loss in energy yield due to climate"
		y = []
		legend = []
		for station in self.stations:
			x = range(1,13)
			y_station = self.climate_loss_accumulated[station]["list"]
			y.append(y_station)
			legend.append(station)
		cfg = {
			"y_zero_line": True,
			"type": "bar",
		}
		self.build_graph(name, "Month", x, "percent", y, legend, cfg)		

	def graph_create_yearly_energy_yield(self):
		name = "Yearly energy yield"
		y = []
		legend = []
		for station in self.stations:
			x = self.energy_yield_list[station]["years_x"]
			y_station = self.energy_yield_list[station]["years_y"]
			y.append(y_station)
			legend.append(station)
		cfg= {
			"type": "plot",
		}
		self.build_graph(name, "Year", x, "yield in %s"%self.rad_unit, y, legend, cfg)




	def build_graph(self, name, x_name, x_coordinates, y_name, y_coordinates, legend, cfg=None):
		N = len(x_coordinates)
		ind = np.arange(N)  # the x locations for the groups

		fig, ax = plt.subplots()


		img = io.BytesIO()
		if type(y_coordinates) == "list":
			print "NO LIST GIVEN FOR GRAPH!"
			return 

		a, i = 0, 0
		width = 1.0/float(len(y_coordinates))-0.05       # the width of the bars
		for y in y_coordinates:
			if cfg["type"] == "bar":
				ax.bar(ind+a, y, width, label=legend[i].title(), zorder=2)
				a += width
			elif cfg["type"] == "plot":
				ax.plot(x_coordinates, y, label=legend[i].title(), zorder=2)
			i += 1

		if cfg:
			if "y_zero_line" in cfg and cfg["y_zero_line"] == True:
				ax.axhline(0, color='black', lw=1, zorder=1)

		ax.set_xlabel(x_name)
		ax.set_ylabel(y_name)
		ax.set_title(name)
		if cfg["type"] == "bar":
			ax.set_xticks(ind + width / 2)
			ax.set_xticklabels(x_coordinates)
		ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=len(legend))		

		# plt.rcParams.update({'font.size': 14})

		fig.tight_layout()
		# fig.set_size_inches(20, 10)

		path_root = os.path.dirname(__file__)
		name = name+"_"+self.label
		path = os.path.join(path_root, "../../../img/%s.png"%name)
		path = os.path.abspath(path)
		fig.savefig(path, dpi=200)
		img.seek(0)
		graph_url = base64.b64encode(img.getvalue()).decode()
		plt.close()
		print "  SAVED IMAGE at "+path
		return 'data:image/png;base64,{}'.format(graph_url)	



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
		# time_series = self.rsds
		out = {}
		for station in self.stations:
			out[station] = {"years":{}, "course":{}}

		self.current_index = 0
		for i in self.rsds:
			self.current_y, self.current_m, self.current_d, self.current_h = i["year"], i["month"], i["day"], i["hour"]/100
			# print y, m, d, h
			if self.current_y == self.current_y:
				for station in self.stations:
					self.current_station = station
					radiation = float(i[station]) * 3.0 / 1000 # convert units
					energy_yield = radiation * PV_PLANT.efficiency_factor * PV_PLANT.area
					if self._climate_loss:
						energy_yield *= (1 - self.calc_climate_loss(PV_PLANT))

					# if self.current_y == 2070 and self.current_m == 5 and station == "wuerzburg":
						# print ".", radiation, energy_yield, 1-self.calc_climate_loss(PV_PLANT), PV_PLANT.efficiency_factor, PV_PLANT.area
					# if self.rad_unit == "kWh/qm":
						# das macht keinen SInn, die Einheit wurde ja bereits umgerechnet
						# energy_yield = energy_yield / 1000.0 * 8760 # convert from W/qm to kWh/qm

					if self.current_y not in out[station]["years"]: 
						out[station]["years"][self.current_y] = energy_yield
						out[station]["course"][self.current_y] = {}
					else:
						out[station]["years"][self.current_y] += energy_yield

					if self.current_m not in out[station]["course"][self.current_y]: 
						out[station]["course"][self.current_y][self.current_m] = energy_yield
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


	def calc_climate_loss(self, PV_PLANT):
		# climate loss is the loss due to high temperature, sediments and rain

		if self.current_station not in self.climate_loss_data:
			self.climate_loss_data[self.current_station] = {}
		if self.current_y not in self.climate_loss_data[self.current_station]:
			self.climate_loss_data[self.current_station][self.current_y] = {}
		if self.current_m not in self.climate_loss_data[self.current_station][self.current_y]:
			self.climate_loss_data[self.current_station][self.current_y][self.current_m] = []
		self.climate_loss = 0


		radiation = float(self.rsds[self.current_index][self.current_station])#* 3.0 / 1000
		temperature = float(self.tas[self.current_index][self.current_station])
		wind = float(self.wind[self.current_index][self.current_station])
		# a[str(self.current_y)+"_"+str(self.current_m)"_"+str(self.current_d)]
		i = 25
		j = 6.84 # 6.11
		temp_din = 25 # this is the temperature of the test in controlled environment
		temp_module = temperature + (radiation / (i + j * wind))
		temp_loss = (temp_module - temp_din) * PV_PLANT.module_temp_koeff / 100
		# print self.current_y
		# if self.current_y == 2071 and self.current_m in [1,6] and self.current_d == 15 and self.current_station=="wuerzburg":
			# print self.current_d, self.current_h, radiation, temperature, temp_module, temp_loss

		# if self.current_m >= 3 and self.current_m <= 9:
			# now do dust and organic pollution
			# check how long no rain is needed to let efficiency sink
			# define a efficiency loss per day without rain?
			# how much rain is needed for cleaning?
			# check x days before now?
			# better: check when last rain set loss to 0, save this time index and start from there, store in self.temporary_data["xxx"]
			# before this function iter through PR and detect first rain event (set to zero) bevore start_month_dust calculation (define in cfg)
			# bei Niederschlag jeden einzelnen Tag betrachten, nicht Durchschnitt (Reinigungswirkung)

		self.climate_loss = temp_loss

		if self._deposit_loss == True:
			i = self.current_index
			if "last_dry_period" not in self.temporary_data:
				self.temporary_data["last_dry_period"] = {}
				self.temporary_data["last_dry_period_temp"] = {}
			# if self.current_station not in self.temporary_data["last_dry_period"]:
			self.temporary_data["last_dry_period_temp"][self.current_station] = [float(self.pr[i][self.current_station])]
			self.temporary_data["last_dry_period"][self.current_station] = False

			while sum(self.temporary_data["last_dry_period_temp"][self.current_station]) < self.climate_loss_cfg["rain_clean_treshold"]:
				i -= 1
				if i < 0:
					break
				# self.temporary_data["last_dry_period_temp"][self.current_station].pop(0)
					
				pr = float(self.pr[i][self.current_station])
				self.temporary_data["last_dry_period_temp"][self.current_station].append(pr)
				self.temporary_data["last_dry_period"][self.current_station] = i
			
			# print self.current_index, self.current_d,self.current_m,  self.current_h
			# print sum(self.temporary_data["last_dry_period_temp"][self.current_station]),len(self.temporary_data["last_dry_period_temp"][self.current_station]), self.temporary_data["last_dry_period_temp"]

			deposit_loss = self.climate_loss_cfg["deposit_loss_timestep"] * len(self.temporary_data["last_dry_period_temp"][self.current_station])
			# print deposit_loss, temp_loss

			# print self.temporary_data["last_dry_period_temp"]
			# print self.get_date_of_index(self.pr[self.temporary_data["last_dry_period"][self.current_station]])

			self.climate_loss += deposit_loss

		self.climate_loss_data[self.current_station][self.current_y][self.current_m].append(self.climate_loss)
		return self.climate_loss


	def get_date_of_index(self, i):
		year = i["year"]
		month = i["month"]
		day = i["day"]
		hour = i["hour"]
		return "%s-%s-%s %s"%(year, month, day, hour)

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

starttime = datetime.datetime.now()

PVMODEL = PVMODEL()


print "ENDE"
print "runtime:", datetime.datetime.now()-starttime
