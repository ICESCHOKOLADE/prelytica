from flask import Blueprint, render_template, abort
import io, csv, base64, os

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

climate_blueprint = Blueprint('climate', __name__)


@climate_blueprint.route('/graphs')
def graphs():
 

	parameter = "rsds"
	model = "rcp85"
	DATA = ClimateData(parameter, model)

	graph_cfg = {
		"locations": ["brand", "wuerz"],
		"start_year": 1970,
		"end_year": 2080,
		"month": 7
	}
	DATA.create_graph_data(graph_cfg)

	x = DATA.graph_data["x"]
	y1 = DATA.graph_data["brand"]
	y2 = DATA.graph_data["wuerz"]
 
	graph1_url = build_graph(x,y1);
	graph2_url = build_graph(x,y2);

	return render_template('graphs/graphs.html',
	graph1=graph1_url,
	graph2=graph2_url)

class ClimateData(object):
	"""docstring for ClimateData"""
	def __init__(self, parameter, model):
		super(ClimateData, self).__init__()
		self.parameter = parameter
		self.model = model
		self.path = "/home/stefan/prelytica/data/climate_model/"
		self.filename = "timeseries_3h_rca4_%s_%s.txt"%(parameter, model)

		# self.start_year = 1970
		# self.end_year = 1975
		# self.month = 6

		self.init_data()
		self.scale = "month"
		self.aggregate_data()


	def create_graph_data(self, cfg):
		self.graph_data = {
			"x": []
		}
		for l in cfg["locations"]:
			self.graph_data[l] = []
		for y in sorted(self.data_dict.iterkeys()):
			y = int(y)
			if y < cfg["start_year"] or y > cfg["end_year"]:
				continue

			self.graph_data["x"].append(y)

			for l in cfg["locations"]:
				x = self.data_dict[str(y)][str(cfg["month"])][l]
				if self.parameter == "rsds":
					x = x * 3 / 1000
					# values are in w/m2, in 3 hour intervals
				# print y, x
				self.graph_data[l].append(round(x,3))

		print self.graph_data





	def aggregate_data(self):
		if self.parameter in ["pr", "rsds"]:
			typ = "sum"
		else:
			typ = "mean"

		
		self.data_dict = {
			# "brand": {},
			# "minde" : {},
			# "amste" : {},
			# "wuerz" : {}	
		}

		brand = "brand"
		minde = "minde"
		amste = "amste"
		wuerz = "wuerz"
		self.locations = {
			"brand": self.data_list[0].index("brand"),
			"minde": self.data_list[0].index("minde"),
			"amste": self.data_list[0].index("amste"),
			"wuerz"	: self.data_list[0].index("wuerz")
		}

		valcount = {}

		index_year = self.data_list[0].index("year")
		index_month = self.data_list[0].index("month")
		index_day = self.data_list[0].index("day")

		for i in self.data_list[1:]:
			if len(i) < 2:
				continue
			if i[index_year] not in self.data_dict:
				self.data_dict[i[index_year]] = {}
				valcount[i[index_year]] = {}
			if i[index_month] not in self.data_dict[i[index_year]]:
				self.data_dict[i[index_year]][i[index_month]] = {}
				valcount[i[index_year]][i[index_month]] = 0

			if self.scale == "month":
				for l in self.locations:
					value = float(i[self.locations[l]])
					if l not in self.data_dict[i[index_year]][i[index_month]]:
						self.data_dict[i[index_year]][i[index_month]][l] = value
					else:
						self.data_dict[i[index_year]][i[index_month]][l] += value
					valcount[i[index_year]][i[index_month]] += 1
			
		if self.scale == "month" and typ == "mean":
			for y in self.data_dict:
				for m in self.data_dict[y]:
					for l in self.locations:
						print y,m, valcount[y][m], self.data_dict[y][m][l]
						self.data_dict[y][m][l] = self.data_dict[y][m][l] / valcount[y][m]

		print "hier muss weiter gearbeitet werden, Temperatur Skala stimmt nicht"

		# print self.data_dict





	def init_data(self):
		f = open(self.path+self.filename,'r')
		message = f.read()
		f.close()
		message = message.replace(";"," ")
		for i in range(10):
			message = message.replace("  "," ")
		message = message.replace(" ",";")
		message = message.replace("\n;","\n")
		if message[0] == ";":
			message = message[1:]
		# print(message)

		mess_list = message.split("\n")
		self.data_list = []
		for i in mess_list:
			x = i.split(";")
			self.data_list.append(x)


def build_graph(x_coordinates, y_coordinates):
	img = io.BytesIO()
	plt.figure(figsize=(17,3))
	plt.plot(x_coordinates, y_coordinates)
	# plt.set_size_inches(18.5, 10.5)
	plt.savefig(img, format='png')
	img.seek(0)
	graph_url = base64.b64encode(img.getvalue()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(graph_url)	