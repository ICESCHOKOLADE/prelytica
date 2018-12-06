# -*- coding: utf-8 -*-
########################
###
### author:     Stefan Rieder
### init_date:     09.02.2018
### topic:         fetch data from pvgis and process it into schema
###
#######################


import requests
import datetime, json
from helper import *
import psycopg2
import psycopg2.extras
# from base import debug
 
debug = False


try:
    conn = psycopg2.connect("dbname='stefan' user='stefan' host='localhost' password='hjkl'")
    # cur = conn.cursor()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

except:
    print "I am unable to connect to the database"



month_english = {
    1:"January",
    2:"February",
    3:"March",
    4:"April",
    5:"May",
    6:"June",
    7:"July",
    8:"August",
    9:"September",
    10:"October",
    11:"November",
    12:"December"
}


class PVGIS_DATA(object):
    """docstring for PVGIS_DATA"""
    def __init__(self, lat, lon, tilt, aspect, gesamtwirkungsgrad):
        super(PVGIS_DATA, self).__init__()
        self.months_init = {"1":{}, "2":{}, "3":{}, "4":{}, "5":{}, "6":{}, "7":{}, "8":{}, "9":{}, "10":{}, "11":{}, "12":{}}
        self.aspect = aspect
        self.tilt = tilt
        self.efficiency = gesamtwirkungsgrad
        self.lat = round(lat,2)
        self.lon = round(lon,2)
        self.yearly_radiation_tilt = 0
        self.yearly_radiation_flat = 0

        self.data_cached = self.check_cached_data()
        if self.data_cached:
            # print "CACHED DATA"
            if debug: print "debug: PVGIS using cached data"
            self.handle_cached_data()
            # print "hhhh", self.pv_hour
        else:
            print "REQUEST PVGIS"
            self.raw_pv_data = self.pvgis_get_pv_values()
            if self.raw_pv_data == 503:
                print "ERROR, NO PV PVGIS DATA"
            # this sets self.pv_month and self.pv_day
            self.process_pvgis_pv("tab_pv")
            # print self.pv_month
            # print self.pv_day

            self.raw_rad_data = self.pvgis_get_rad_values()
            if self.raw_rad_data == 503:
                print "ERROR, NO PV PVGIS DATA"
            # this sets self.rad_month
            self.process_pvgis_pv("tab_rad")
            # self.pvgis_scaffold_factor = get_pvgis_scaffold_factor(self.pvgis_rad_monthly)
            # print ".........", self.rad_month

            # self.pv_hour = self.months_init.copy()
            # if "Year" in self.pv_hour:
            #     del self.pv_hour["Year"]
            self.raw_day_data = {}
            self.pv_hour = {}
            for m in range(1,13):
                self.raw_day_data[m] = self.pvgis_4_get_daily_values(m)
                self.process_pvgis_daily(m)
            
            self.set_cache_data()

        self.calculate_year_percentage()

        # http://re.jrc.ec.europa.eu/pvgis5/seriescalc.php?lat=50.000&lon=+9.000&raddatabase=PVGIS-CMSAF&browser=1&userhorizon=&usehorizon=1&angle=30&azimuth=0&startyear=2016&endyear=2016&mountingplace=&optimalinclination=0&optimalangles=0&select_database_hourly=PVGIS-CMSAF&hstartyear=2016&hendyear=2016&trackingtype=0&hourlyangle=30&hourlyaspect=0&components=1


    def calculate_year_percentage(self):
        self.global_climate_percentage = {
            "month":{}, 
            "day":{},
            "hour": {}
        }
        c = {}
        pvgis_year_sum, pvgis_month_sum = 0,0

        for m in self.pv_month:
            self.global_climate_percentage[m] = {}
            self.global_climate_percentage["day"][m] = 0
            self.yearly_radiation_tilt += self.pv_month[m]
            for h in self.pv_hour[m]:
                # those day values are not in kWh but kW per quarter hour
                # calculate monthly percentages
                self.global_climate_percentage["day"][m] += self.pv_hour[m][h] / 4
        for m in self.pv_month:
            self.global_climate_percentage["hour"][m] = {}
            for h in self.pv_hour[m]:
                self.global_climate_percentage["hour"][m][h] = self.pv_hour[m][h] / 4 / self.yearly_radiation_tilt
            self.global_climate_percentage["month"][m] = round(self.pv_month[m] / self.yearly_radiation_tilt, 6)


        for m in self.rad_month:
            self.yearly_radiation_flat += self.rad_month[m]
        self.yearly_radiation_flat = self.yearly_radiation_flat / 1000.0 /12 * 356.25   # sum is for 12 days, so calc for year sum and convert to kWh
        self.tilt_flat_ratio = self.yearly_radiation_tilt / self.yearly_radiation_flat
        # print self.yearly_radiation_flat, self.yearly_radiation_tilt, self.tilt_flat_ratio
        # print "---", self.global_climate_percentage["hour"]["1"]
        # print "...", self.global_climate_percentage["month"]["1"]
        # print self.yearly_radiation_tilt, self.pv_month["1"], self.pv_hour["1"]["11"]
        if debug:
            print "Yearly radiation on this roof is:", self.yearly_radiation_tilt, "kWh/m²", self.tilt, self.aspect






    def process_pvgis_daily(self, m):
        self.pv_hour[m] = {}
        a = self.raw_day_data[m].replace("\t\t",";").replace("\r","").split("Gd")[1].split("G:")[0]
        for i in a.split("\n"):
            if len(i) < 3:
                continue
            x = i.split(";")
            h = int(x[0].split(":")[0])
            if str(h) not in self.pv_hour[m]:
                self.pv_hour[m][str(h)] = 0
            # h = int(i[0].split(":")[0])+1 # 22:45 -> 23
            self.pv_hour[m][str(h)] += round(float(x[1])/1000.0,6) # in PVGIS: this is W/sqm, not kWh!


    def set_cache_data(self):
        query = """ INSERT INTO cache_pvgis (type, data, lat, lon, tilt, aspect)
                    VALUES ('%s', '%s', %s, %s, %s, %s), ('%s', '%s', %s, %s, %s, %s), ('%s', '%s', %s, %s, %s, %s), ('%s', '%s', %s, %s, %s, %s)
                     """%("pv_day", json.dumps(self.pv_day), self.lat, self.lon, self.tilt, self.aspect, \
                        "pv_month", json.dumps(self.pv_month), self.lat, self.lon, self.tilt, self.aspect, \
                        "pv_hour", json.dumps(self.pv_hour), self.lat, self.lon, self.tilt, self.aspect, \
                        "rad_month", json.dumps(self.rad_month), self.lat, self.lon, self.tilt, self.aspect)
        # print query
        print "- only setting pv data (orientated)"
        cur.execute(query)        

        conn.commit()


    def handle_cached_data(self):
        for i in self.data_cached:
            if i["type"] == "pv_day":
                self.pv_day = i["data"]
            elif i["type"] == "pv_month":
                self.pv_month = i["data"]
            elif i["type"] == "pv_hour":
                self.pv_hour = i["data"]        
                # print i["data"]
            elif i["type"] == "rad_month":
                self.rad_month = i["data"]
            else:
                print "AND NOW? Data from cache is not set"


    def check_cached_data(self):
        query = """SELECT type, data FROM cache_pvgis WHERE lat = %s AND lon = %s AND tilt = %s AND aspect = %s """%(self.lat, self.lon, self.tilt, self.aspect)
        cur.execute(query)
        data_cached = cur.fetchall()
        # print query
        if not data_cached:
            data_cached = None

        # print type(data_cached)
        # print data_cached
        return data_cached

    def process_pvgis_pv(self, name):
        repl = {"Jan":"1","Feb":"2","Mar":"3","Apr":"4","May":"5","Jun":"6","Jul":"7","Aug":"8","Sep":"9","Oct":"10","Nov":"11","Dec":"12"}

        if name == "tab_pv":
            self.pv_month = self.months_init.copy()
            self.pv_day = self.months_init.copy()
            data_in = self.raw_pv_data
            result = data_in.replace("\t",",").replace("\n",";").replace("\r","").split("Hm")[1].split("Ed:")[0].replace(",,",",").replace(";;",";")
        elif name == "tab_rad":
            self.rad_month = self.months_init.copy()
            data_in = self.raw_rad_data
            result = data_in.replace("\t",",").replace("\n",";").replace("\r","").split("Hh")[1].replace(",,",",").replace(";;",";").replace(" ","")
            for key in repl:
                result = result.replace(key, repl[key])
        values = result.split(";")
        i = 0
        for j in values: 
            if len(j) < 1:
                del values[i]
            i=i+1
        i=0
        for val in values:
            v = val.encode("utf-8").split(",")
            if v[0] != "Year":
                if name == "tab_pv":
                    self.pv_day[str(v[0])] = float(v[3])
                    self.pv_month[str(v[0])] = float(v[4])
                else:
                    self.rad_month[str(v[0])] = int(v[1])
            i = i+1


        for m in self.pv_month:
            # make keys to integer
            self.pv_month[int(m)] = self.pv_month.pop(m)


    def pvgis_get_pv_values(self):
        # in actual version only Hm (Average sum of global irradiation per square meter received by the modules of 
        # the given system (kWh/m2)) is used, so some params like loss have no influence
        url = "http://139.191.1.113"
        url_2 = "http://re.jrc.ec.europa.eu"
        data = {'regionname': 'europe',
                 'pv_database': 'PVGIS-CMSAF',
                 'MAX_FILE_SIZE': '10000',
                 'pvtechchoice': 'crystSi',
                 'peakpower': 1,
                 'efficiency': self.efficiency * 100,
                 'mountingplace': 'building',
                 'angle': self.tilt,
                 'aspectangle': self.aspect,
                 'outputchoicebuttons': 'text',
                 'sbutton': 'Calculate',
                 'outputformatchoice': 'csv',
                 'optimalchoice': '',
                 'latitude': str(self.lat),
                 'longitude': str(self.lon),
                 'regionname': 'europe',
                 'language': 'en_en'
            }
        try:
            result = requests.post('%s/pvgis/apps4/PVcalc.php'%url, data, files={})
        except:
            try:
                result = requests.post('%s/pvgis/apps4/PVcalc.php'%url, data, files={})
            except:
                return 503

        # print result.text
        return result.text


    def pvgis_get_rad_values(self):
        # only irradiation on horizontal plane (Wh/m2/day)
        url = "http://139.191.1.113"
        url_2 = "http://re.jrc.ec.europa.eu"    
        data = {'regionname': 'europe',
                 'mr_database': 'PVGIS-CMSAF',
                 'horirrad': 'true',
                 'optrad': 'false',
                 'selectrad': 'false',
                 'monthradangle': '30',
                 'optincl': 'false',
                 'avtemp': 'false',
                 'degreedays': 'false',
                 'outputchoicebuttons': 'text',
                 'sbutton': 'Calculate',
                 'outputformatchoice': 'csv',
                 'optimalchoice': '',
                 'latitude': str(self.lat),
                 'longitude': str(self.lon),
                 'regionname': 'europe',
                 'language': 'en_en'
                 }

        try:
            result = requests.post('%s/pvgis/apps4/MRcalc.php'%url, data)
        except:
            try:
                result = requests.post('%s/pvgis/apps4/MRcalc.php'%url, data)
            except:
                return 503
        return result.text


    def pvgis_4_get_daily_values(self, month):
        month_word = month_english[month]
        url = "http://re.jrc.ec.europa.eu"    
        data = {
                "region": "europe",
                "dr_database": 'PVGIS-CMSAF',
                'sbutton': 'Calculate',
                'outputformatchoice': 'csv',
                 'outputchoicebuttons': 'text',
                "global": 1,
                "month": month_word,
                 'lat': str(self.lat),
                 'lon': str(self.lon),                
                "DRangle": self.tilt,
                "DRaspectangle": self.aspect,
                "angle": self.tilt,
                "aspect": self.aspect
                 }

        try:
            result = requests.get('%s/pvgis/apps4/DRcalc.php'%url, data)
            # print "....", result.text
        except:
            return 503
        return result.text


    def pvgis_5_get_daily_values(self, month):
        url = "http://re.jrc.ec.europa.eu"    
        data = {
                "lat": str(self.lat),
                "lon": str(self.lon),
                "raddatabase": 'PVGIS-CMSAF',
                "outputformat": 'basic',
                "browser": 0,
                "month": month,
                "usehorizon": 1,
                "userhorizon": "True",
                "localtime": 0,
                "global": 1,
                "angle": self.tilt,
                "aspect": self.aspect,
                "glob_2axis": 1
                 }

        try:
            result = requests.get('%s/pvgis5/DRcalc.php'%url, data)
        except:
            return 503
        return result.text