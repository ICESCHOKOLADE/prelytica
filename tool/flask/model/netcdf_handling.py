# -*- coding: utf-8 -*-
from netCDF4 import Dataset, num2date, date2num, date2index
import numpy as np
import datetime as dt
from netcdf_write import NETCDF_OUTPUT


lat = 49.7
lon = 9.9
month = 1
year = 1972
day = 15
parameter = "rsds"

"""
https://stackoverflow.com/questions/18665078/loop-through-netcdf-files-and-run-calculations-python-or-r
https://stackoverflow.com/questions/56455165/how-do-loop-over-netcdf-timeseries/56456069#56456069

"""


# a function to find the index of the point closest pt
# (in squared distance) to give lat/lon value.
def getclosest_ij(lats,lons,latpt,lonpt):
		# find squared distance of every point on grid
		dist_sq = (lats-latpt)**2 + (lons-lonpt)**2 
		# 1D index of minimum dist_sq element
		minindex_flattened = dist_sq.argmin()
		# Get 2D index for latvals and lonvals arrays from 1D index
		return np.unravel_index(minindex_flattened, lats.shape)
 
 

def get_netcdf_data_for_date(lat, lon, parameter, date):
		path = "C:/Users/NN/Desktop/netcdf/"
		file = "%s_daymean.nc"%(parameter)
		filepath = path+file
		dataset = Dataset(filepath)
		data_key = dataset.variables.keys()[-1]
		data = dataset.variables[data_key]
		latvals, lonvals = dataset.variables['lat'][:], dataset.variables['lon'][:]
		#print dataset
		#print "Dimensions:", dataset.variables.keys()
		# print data

		# now get position index in tuples of requested point
		index_lat, index_lon = getclosest_ij(latvals, lonvals, lat, lon)

		# time is always (?) first data entry, so keep this
		time_key = data.dimensions[0] 
		times = dataset.variables[time_key] 
		# print('units = %s, values = %s' % (times.units, times[:]))
		dates = num2date(times[:], times.units)
		# print([datum.strftime('%Y-%m-%d %H:%M:%S') for datum in dates]) 
		# print dates[:]

		# now convert date from given string, to search in data
		date = dt.datetime.strptime(date, '%Y-%m-%d')
		# print date
		ntime = date2index(date, times, select='nearest', calendar="360_day")
		# print('index = %s, date = %s' % (ntime, dates[ntime]))

		# get tuple that fits all retrieved indices
		result = data[ntime, index_lat, index_lon]
		# print result, "for", date

		# print data[:, index_lat, index_lon]
		# print len(times)
		# for i in times:
				# print i#, data[i, index_lat, index_lon]

		if parameter == "tas" and data.units == "K":
				result -= 273.15
		return result



while month <= 12:
		date = "%s-%s-%s"%(str(year), str(month), str(day))
		data = get_netcdf_data_for_date(lat, lon, "tas", date)
		# print "  >>", date, data
		month += 1
# date = "1970-5-15"
# data = get_netcdf_data_for_date(lat, lon, parameter, date)




path = "C:/Users/NN/Desktop/netcdf/"
file = "%s_daymean.nc"%(parameter)
newfile = path+"test.nc"
filepath = path+file
dataset = Dataset(filepath)
data_key = dataset.variables.keys()[-1]
data = dataset.variables[data_key]
# lat = dataset.variables['lat']
# lon = dataset.variables['lon']
# out = NETCDF_OUTPUT(lon, lat)
# out.write_data()




class FileHandler(object):
	"""docstring for FileHandler"""
	def __init__(self, filename, target):
		super(FileHandler, self).__init__()
		self.path = "C:/Users/NN/Desktop/netcdf/"

		self.filename = filename
		self.target = target

		self.rsds = Dataset(self.filename)
		self.dst = Dataset(self.target, "w")
		# self.rsds_2 = Dataset(self.path + "rsds_daymean.nc")
		self.temperature = Dataset(self.path + "tas_daymean.nc")
		self.wind = Dataset(self.path + "sfcWind_daymean.nc")


		self.new_name = "TEST"
		
	def copy_existing_file(self):
		to_exclude = []
		copy = [] #["rsds"]

		with self.rsds, self.dst:
			# copy global attributes all at once via dictionary
			self.dst.setncatts(self.rsds.__dict__)
			# copy dimensions
			for name, dimension in self.rsds.dimensions.iteritems():
				self.dst.createDimension(
					name, (len(dimension) if not dimension.isunlimited() else None))
			# copy all file data except for the excluded
			for name, variable in self.rsds.variables.iteritems():
				if name not in to_exclude:
					self.copy_variable(variable, name)
					if name in copy:
						self.copy_variable(variable, self.new_name)


					# if name in ["rsds"]:
					# 	print dst[target_name].dimensions
					# 	for dim in dst[target_name].dimensions:
					# 		print dst[dim].shape
		print ">>> COPYING of", self.filename, "TO", self.target, "SUCCESSFUL"
		print ">>> REMOVED: ", to_exclude


		self.do_climate_loss_calculations()

	def do_climate_loss_calculations(self):
		dataset = Dataset(self.target, "a", format='NETCDF4')

		test = dataset.createVariable("test", 'f4', ('time', 'rlat', 'rlon'))
		temperature_module = dataset.createVariable("module temperature", 'f4', ('time', 'rlat', 'rlon'))
		temperature_loss = dataset.createVariable("temperature loss", 'f4', ('time', 'rlat', 'rlon'))


		test[:] = np.add(self.rsds["rsds"], self.rsds["rsds"])

		i = 25
		j = 6.84 # 6.11
		temp_din = 25 # this is the temperature of the test in controlled environment
		temp_coeff = 0.5 / 100 # % per K
		# radiation * 3 / 1000 = 0.003 (to other unit)
		# temperature_module[:] = temperature + (radiation / (i + j * wind))
		temperature_module[:] = np.add(np.add(self.temperature["tas"],-273.15), np.divide(np.multiply(self.rsds["rsds"], 0.003), np.add(np.multiply(self.wind["sfcWind"], j), i)))
		print "   note, that module temperature could not be calculated with mean values (of months or days)"
		# temp_loss = (temp_module - temp_din) * PV_PLANT.module_temp_koeff / 100		
		temperature_loss[:] = np.multiply(np.subtract(temperature_module[:], temp_din), temp_coeff)


		print "To DO: wait for data with higher temporal resolution"
		print "TO DO: prepare drought calculation for pollution loss"


		dataset.close()
		print ">>> FINISHED: wrote data to", self.target

	def copy_variable(self, variable, target_name):
		x = self.dst.createVariable(target_name, variable.datatype, variable.dimensions)
		for attr in self.rsds[variable.name].ncattrs():            
			# copy variable attributes all at once via dictionary
			self.dst[target_name].setncattr(attr, getattr(self.rsds[variable.name],attr))
		# set data
		self.dst[target_name][:] = self.rsds[variable.name][:]		




fh = FileHandler(filepath, newfile)
fh.copy_existing_file()

