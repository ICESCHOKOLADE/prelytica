# -*- coding: utf-8 -*-

from datetime import datetime
import netCDF4 as nc4
import numpy as np

"""
basic netcdf writing
http://unidata.github.io/netcdf4-python/
https://iescoders.com/2017/10/03/reading-netcdf4-data-in-python/
http://pyhogs.github.io/intro_netcdf4.html
"""

class NETCDF_OUTPUT(object):
	"""docstring for NETCDF_OUTPUT"""
	def __init__(self, lon, lat):
		super(NETCDF_OUTPUT, self).__init__()
		today = datetime.today()
		print ">>> OPENED NETCDF WRITING"

		# self.lon = np.arange(45,101,2)
		# self.lat = np.arange(-30,25,2)
		self.lon = lon
		self.lat = lat


		self.path = "C:/Users/NN/Desktop/netcdf/"
		self.file = "test_output.nc"
		self.description = "Example dataset containing one group"
		self.history = "Created " + today.strftime("%d/%m/%y")
		self.group_name = "Solar loss model"
		self.data_name = "Temperature"
		self.data_unit = "Kelvin"
		self.data_hint = "Attention"
		self.time_units = "days since 01.01.0001"

	def validate_data(self):
		# if not self.max_lon: return False
		# if not self.min_lon: return False
		# if not self.max_lat: return False
		# if not self.min_lat: return False
		# if not self.data: return False
		# if not self.time: return False
		# if not self.lon: return False
		# if not self.lat: return False
		return True



	def write_data(self):
		if not self.validate_data():
			return None


		f = nc4.Dataset(self.path + self.file,'w', format='NETCDF4') #'w' stands for write
		tempgrp = f.createGroup(self.group_name)

		tempgrp.createDimension('lon', len(self.lon[:][0]))
		tempgrp.createDimension('lat', len(self.lat[:]))
		tempgrp.createDimension('time', None)

		longitude = tempgrp.createVariable('lon', 'f4', 'lon')
		latitude = tempgrp.createVariable('lat', 'f4', 'lat')  
		# longitude = self.lon
		# latitude = self.lat
		data = tempgrp.createVariable(self.data_name, 'f4', ('time', 'lon', 'lat'))
		time = tempgrp.createVariable('Time', 'i4', 'time')

		print tempgrp.dimensions
		print self.lon[:][0]
		print self.lat[:][1]
		longitude[:] = self.lon[:][0] #The "[:]" at the end of the variable instance is necessary when creating from numpy array
		latitude[:] = self.lon[:][0]
		# print "...", self.lat[0]

		for x in range(0,200):
			temp_data = np.random.randint(0,40, size=(len(self.lon[:][0]), len(self.lat[:])))
			data[x,:,:] = temp_data
			today = datetime.today()
			time_num = today.toordinal() # rechnet Tage seit erstem Tag des gregorianischen Kalenders inkl. Enddatum (seit 1.1.1)
			time[x] = x

		#Add global attributes
		f.description = self.description
		f.history = self.history

		#Add local attributes to variable instances
		# longitude.units = 'degrees east'
		# latitude.units = 'degrees north'
		time.units = self.time_units
		data.units = self.data_unit
		data.hint = self.data_hint
		data.coordinates = "lat lon"


		print ">>> NETCDF FILE HAS BEEN WRITTEN"
		f.close()



# out = NETCDF_OUTPUT()
# out.write_data()