from server import *
import requests
import json


def tetraeder_api(hid, args=None):
	url = "https://detailskronos.solare-stadt.de/hub/api/id_search/stadt_brandenburg/%s/?rooflist"%hid
	username = "th_brandenburg"
	password = "675tokJSVq2X"
	if "energy_consumption" in args:
		url = url + "&energy_consumption=%s"%args["energy_consumption"]
	if "load_profile" in args:
		url = url + "&load_profile=%s"%args["load_profile"]		
	r = requests.get(url, auth=(username, password))
	if r.status_code == 200:
		return r.json()
	else:
		print r.status_code
