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
	def __init__(self):
		super(NETCDF_OUTPUT, self).__init__()

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

		lon = np.arange(45,101,2)
		lat = np.arange(-30,25,2)
		print lon
		print lat
		temp_data = np.random.randint(0,40, size=(len(lon), len(lat)))


		f = nc4.Dataset(self.path + self.file,'w', format='NETCDF4') #'w' stands for write
		tempgrp = f.createGroup(self.group_name)

		tempgrp.createDimension('lon', len(lon))
		tempgrp.createDimension('lat', len(lat))
		tempgrp.createDimension('time', None)

		longitude = tempgrp.createVariable('Longitude', 'f4', 'lon')
		latitude = tempgrp.createVariable('Latitude', 'f4', 'lat')  
		data = tempgrp.createVariable(self.data_name, 'f4', ('time', 'lon', 'lat'))
		time = tempgrp.createVariable('Time', 'i4', 'time')


		longitude[:] = lon #The "[:]" at the end of the variable instance is necessary
		latitude[:] = lat

		for x in range(0,200):
			data[x,:,:] = temp_data
			today = datetime.today()
			time_num = today.toordinal() # rechnet Tage seit erstem Tag des gregorianischen Kalenders inkl. Enddatum (seit 1.1.1)
			time[x] = x

		#Add global attributes
		f.description = self.description
		f.history = self.history

		#Add local attributes to variable instances
		longitude.units = 'degrees east'
		latitude.units = 'degrees north'
		time.units = self.time_units
		data.units = self.data_unit
		data.hint = self.data_hint

		f.close()



out = NETCDF_OUTPUT()
out.write_data()