########################
###
### author: 	Stefan Rieder
### init_date: 	09.02.2018
### topic: 		small helper functions
###
#######################

import calendar



def get_monthly_day_count(year, month):
    coun = calendar.monthrange(int(year), int(month))[1]
    return int(coun)