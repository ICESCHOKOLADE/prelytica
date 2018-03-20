from flask import Flask,render_template, jsonify, request
app = Flask(__name__)

@app.route('/')
def home():
   return "This is my home"

@app.route('/solarpotential_id/<hid>')
def test(hid):
	from data_view import tetraeder_api

	raw_data = tetraeder_api(hid, request.args)
	return render_template("show_api_data.html", data=raw_data)
	return jsonify(raw_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)