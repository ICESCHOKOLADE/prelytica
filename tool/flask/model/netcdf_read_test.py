from netCDF4 import Dataset, num2date, date2num, date2index
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

"""
basic netcdf reading
http://unidata.github.io/netcdf4-python/
https://iescoders.com/2017/10/03/reading-netcdf4-data-in-python/
"""

lat = 49.7
lon = 9.9
month = 1
year = 1972
day = 15
parameter = "rsds"


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
	file = "%s_monmean.nc"%(parameter)
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
	print "  >>", date, data
	month += 1
date = "1970-5-15"
data = get_netcdf_data_for_date(lat, lon, parameter, date)
# print date,":", data

cs = plt.contourf(data[0,0,::-1,:] )
