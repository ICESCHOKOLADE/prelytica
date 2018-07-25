import csv



class HISTORIC_DATA(object):
	def __init__(self, building):
		super(HISTORIC_DATA, self).__init__()

		# self.lat = lat
		# self.lon = lon
		# self.args = args
		self.path = "/home/stefan/prelytica/tool/flask/data/historic/radiation/"
		self.filename = "52.41,12.54.csv"
		self.file = self.path + self.filename

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