# -*- coding: utf-8 -*-
#!/usr/bin/python
import psycopg2
import sys
import pprint

import csv

parameter = "tas"
model = "rcp85"

path = "data/climate_model/"
filename = "timeseries_3h_rca4_%s_%s.txt"%(parameter, model)
tempfile = path+filename

parameter = "pr"
filename = "timeseries_3h_rca4_%s_%s.txt"%(parameter, model)
prfile = path+filename

def init_data(file):
	f = open(file,'r')
	message = f.read()
	f.close()
	message = message.replace(";"," ")
	for i in range(10):
		message = message.replace("  "," ")
	message = message.replace(" ",";")
	message = message.replace("\n;","\n")
	if message[0] == ";":
		message = message[1:]
	# return message

	mess_list = message.split("\n")
	data_list = []
	for i in mess_list:
		x = i.split(";")
		data_list.append(x)

	return data_list




class HEATING(object):
	"""docstring for HEATING"""
	def __init__(self):
		super(HEATING, self).__init__()

		# self.arg = arg
		self.summer_start = 5
		self.summer_end = 8
		self.control_years_start = 1970
		self.control_years_end = 2000
		self.research_years_start = 2070
		self.research_years_end = 2100
		self.id_col = 0
		self.year_col = 1
		self.month_col = 2
		self.day_col = 3
		self.hour_col = 4
		self.stations = {
			# "brandenburg": {
			# 	"col": 5
			# },
			# "minden": {
			# 	"col": 6
			# },
			# "amsterdam": {
			# 	"col": 7
			# },
			"wuerzburg": {
				"col": 8
			}
		}
		self.result = {
			"mean_temperature_control": {},
			"mean_max_temperature_control": {}
		}

		"""
		stated in Jacob 2014 S.4
		
		SELECT avg(wuerzburg) FROM
			(SELECT year, month, day, avg(wuerzburg) as wuerzburg
			FROM tas_rcp85 
			WHERE year > 1969 AND year < 2001
			AND month > 4 AND month < 9
			GROUP BY year, month, day) 
		AS a;

		SELECT avg(wuerzburg) FROM
			(SELECT year, month, day, max(wuerzburg) as wuerzburg
			FROM tas_rcp85 
			WHERE year > 1969 AND year < 2001
			AND month > 4 AND month < 9
			GROUP BY year, month, day) 
		AS a;

		"""

		print "INIT TEMP DATA"
		self.temp_data = init_data(tempfile)
		print "INIT TEMP DATA FINISHED"

		print "CALC MEAN CONTROL DATA"
		self.get_control_mean_temp()
		print "CALC MEAN CONTROL DATA FINISHED"

		print "CALC HEATING WAVES"
		# self.get_heating_waves()
		print "CALC HEATING WAVES FINISHED"


		print "INIT PR DATA"
		# self.pr_data = init_data(prfile)
		print "INIT PR DATA FINISHED"

		print "CALC DROUGHTS"
		# self.calc_droughts()
		print "CALC DROUGHTS FINISHED"
		print self.result

	def get_control_mean_temp(self):
		tmp = {}
		for i in self.temp_data[1:]:
			if len(i) < 3:
				continue
			year = int(i[self.year_col])
			month = int(i[self.month_col])
			day = int(i[self.day_col])
			if month >= self.summer_start and month <= self.summer_end:
				if year >= self.control_years_start and year <= self.control_years_end:
					for station in self.stations:
						temperature = float(i[self.stations[station]["col"]])
						if "list_"+station not in self.result["mean_temperature_control"]:
							self.result["mean_temperature_control"]["list_"+station] = [temperature]
						else:
							self.result["mean_temperature_control"]["list_"+station].append(temperature)

						# now we need the daily max to calc mean max temperature

						if station not in tmp:
							tmp[station] = {}
						if str(year)+str(month)+str(day) not in tmp[station]:
							tmp[station][str(year)+str(month)+str(day)] = temperature
						elif temperature > tmp[station][str(year)+str(month)+str(day)]:
							tmp[station][str(year)+str(month)+str(day)] = temperature

		# print tmp
		for station in self.stations:
			self.result["mean_temperature_control"][station] = sum(self.result["mean_temperature_control"]["list_"+station]) / float(len(self.result["mean_temperature_control"]["list_"+station]))
			del self.result["mean_temperature_control"]["list_"+station]

			t = []
			for i in tmp[station]:
				t.append(tmp[station][i])
			# print "........", t
			self.result["mean_max_temperature_control"][station] = sum(t) / float(len(t))


	def calc_droughts(self):
		dr = {}
		for i in self.pr_data[1:]:
			if len(i) < 3:
				continue			
			year = int(i[self.year_col])
			month = int(i[self.month_col])
			day = int(i[self.day_col])
			if year not in dr:
				dr[year] = {}
			if month not in dr[year]:
				dr[year][month] = {}
			if day not in dr[year][month]:
				dr[year][month][day] = {}
			for station in self.stations:
				precipitation = float(i[self.stations[station]["col"]])
				if station not in dr[year][month][day]:
					dr[year][month][day][station] = precipitation
				else:
					dr[year][month][day][station] += precipitation

		print dr[2020][8]


	def get_heating_waves(self):
		tmp = {}
		r = {}


		for i in self.temp_data[1:]:
			if len(i) < 2:
				continue
			year = int(i[self.year_col])
			month = int(i[self.month_col])
			day = int(i[self.day_col])
			if month >= self.summer_start and month <= self.summer_end:
				if year >= self.research_years_start and year <= self.research_years_end:
					for station in self.stations:
						temperature = float(i[self.stations[station]["col"]])
						if station not in tmp:
							tmp[station] = {}
							r[station] = []
							r[station+"-date"] = []

						if str(year)+"-"+str(month)+"-"+str(day) not in tmp[station]:
							tmp[station][str(year)+"-"+str(month)+"-"+str(day)] = temperature
						elif temperature > tmp[station][str(year)+"-"+str(month)+"-"+str(day)]:
							tmp[station][str(year)+"-"+str(month)+"-"+str(day)] = temperature


		x = {}
		for station in tmp:
			for date in tmp[station]:
				# print date
				r[station].append(tmp[station][date])
				r[station+"-date"].append(date)

			print r["wuerzburg"][0:10]
			print r["wuerzburg-date"][0:10]


		print "hier ist es noch lange nicht fertig. Tage sind nicht sortiert (durch dict), man müsste zwei Listen erstellen, eine Indexliste und eine für Temperaturen"


# HEATING()




def db_connect():
	conn_string = "host='localhost' dbname='postgres' user='postgres' password='tra74ag+'"
	try:
		conn = psycopg2.connect(conn_string)
		cursor = conn.cursor()
	except:
		print "CAN NOT CONNECT TO DB" + conn_string
 
	cursor.execute("SELECT * FROM tas_rcp85")
 	a = cursor.fetchall()
 
	print a[1]
 
if __name__ == "__main__":
	db_connect()