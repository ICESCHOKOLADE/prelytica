# -*- coding: utf-8 -*-
########################
###
### author:     	Stefan Rieder
### init_date:     09.08.2018
### topic:         historic data from meteomatics
###
#######################



import os.path
import csv
# import external_api_meteomatics as meteomatics
import urllib2, base64
from helper import *


class HISTORIC_DATA(object):
	def __init__(self, building):
		super(HISTORIC_DATA, self).__init__()

		self.lat = round(building.lat,1)
		self.lon = round(building.lon,1)
		# self.args = args
		self.path = "/home/stefan/prelytica/data/historic/radiation/"
		self.filename = "%s,%s.csv"%(self.lat, self.lon)
		self.file = self.path + self.filename
		self.meteomatics_data = self.get_data_from_meteomatics()

		self.historic_flat = self.get_historic_flat()
		self.historic_year_sum_flat = {}
		for y in self.historic_flat:
			self.historic_year_sum_flat[y] = self.get_year_sum(y)


	def get_year_sum(self, year):
		global_sum = 0
		for m in self.historic_flat[year]:
			for d in self.historic_flat[year][m]:
				for h in self.historic_flat[year][m][d]:
					global_sum += self.historic_flat[year][m][d][h]

		return global_sum


	def get_historic_flat(self):
		historic_flat = {}
		with open(self.file) as csvfile:
			reader = csv.reader(csvfile, delimiter=';')
			next(reader, None)  # skip the headers
			for row in reader:
				datestamp = row[0]
				radiation = round(float(row[1])/1000.0,4) # convert W in kW
				date = datestamp.split("T")[0].split("-")
				year = int(date[0])
				month = int(date[1])
				day = int(date[2])
				hour = int(datestamp.split("T")[1][:2])
				# print date, hour
				if year not in historic_flat:
					historic_flat[year]={}
				if month not in historic_flat[year]:
					historic_flat[year][month] = {}
				if day not in historic_flat[year][month]:
					historic_flat[year][month][day] = {}
				historic_flat[year][month][day][hour] = radiation
		return historic_flat


	def meteomatics_cached(self):
		if os.path.isfile(self.file):
			return True
		else:
			return False

	def get_data_from_meteomatics(self):
		auth = get_auth_data("meteomatics")

		if self.meteomatics_cached():
			return 

		url = "http://api.meteomatics.com/2015-01-01T00:00:00Z--now:PT1H/global_rad:W/%s,%s/csv "%(self.lat, self.lon)
		print url

		request = urllib2.Request(url)
		base64string = base64.b64encode('%s:%s' % (auth["username"], auth["password"]))
		request.add_header("Authorization", "Basic %s" % base64string)   
		result = urllib2.urlopen(request)
		download = result.read()


		file = open(self.file,"w") 
		file.write(download) 	 
		file.close() 

