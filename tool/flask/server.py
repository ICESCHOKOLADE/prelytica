from flask import Flask,render_template, jsonify, request
import calculator.base as CALC
app = Flask(__name__)

@app.route('/')
def home():
   return "This is my home"

@app.route('/solarpotential_id/<hid>')
def test(hid):
	from data_view import tetraeder_api

	raw_data = tetraeder_api(hid, request.args)
	return render_template("show_api_data.html", data=raw_data)

@app.route('/start')
def start():


	return render_template("tool_start.html")



@app.route('/tool_request')
def tool_request():

	print request.args
	args = request.args

	lat = 52.402958
	lon = 12.506151
	if "lat" in request.args:
		lat = float(request.args["lat"])
	if "lon" in request.args:
		lon = float(request.args["lon"]	)

	# args = {
	# 	"load_profile": "g2",
	# 	"energy_consumption": 30000
	# }

	calculator = CALC.Master(lat, lon, args)
	data = calculator.get_export_data()

	return jsonify(data)



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



