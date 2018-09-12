var kwh_yield_hour;
var results = {};
var chart;
var c = 0;
var month_word = {
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
};
$(document).ready(function(){	

	$("#argument_form").submit(function(e){
		$("#ajax_loader").show();
	    $.ajax({
	           type: "GET",
	           url: "tool_request",
	           data: $("#argument_form").serialize(),
	           dataType: "json",
	           async:true,  
	           success: function(data){
	           		console.log(data);
	           		results[c+1] = data;
					setTimeout(function(){
					  	$("#ajax_loader").hide();
	    				handle_result_data(c);
					}, 1000);

					if (c != 0) {
						$("#add_diagram_form #result_nr").append("<option value='"+(c+1)+"'>"+(c+1)+"</option>")
					}
	           		c=c+1;
					$("#radiation_image").attr("src",data["tetraeder_data"]["results"][0]["images"]["radiation"]);
					$("#roof_image").attr("src",data["tetraeder_data"]["results"][0]["images"]["roofs"]);
	    			$("._area_suited").html(data["tetraeder_data"]["results"][0]["data"]["pv_area_well_suited"] + data["tetraeder_data"]["results"][0]["data"]["pv_area_suited"]);


	           }
	         });
	    e.preventDefault(); 
	});




	$("#add_diagram_form").submit(function(e){
		e.preventDefault();
		data_type = $('#data_type option:selected').val();
		month = $('#month option:selected').val();
		result_nr = $('#result_nr option:selected').val();
		year = $('#year option:selected').val();
		// console.log(result_nr, data_type, year, month);
		if (data_type=="kwh_yield") {
			data = results[result_nr][data_type]["hour"][month];
		}else if (data_type=="kwh_yield_historic") {
			data = results[result_nr]["kwh_yield"]["historic"][parseInt(year)][parseInt(month)][15];
		} else{
			data = results[result_nr][data_type][month];
		}
		title = result_nr+"_"+month_word[month]+"_"+data_type ;
		title = title.replace("kwh_yield", "Solarertrag");
		title = title.replace("load_profile", "Lastprofil");
		// console.log(data);
		add_to_diagram(data, title);
	});

	$("#reset_diagram").click(function(){
		reset_diagram();
	});


	function handle_result_data(c) {
	    kwh_yield_hour = results[c]["kwh_yield"]["hour"];
	    if (c == 1) {
	    	show_hour_diagram(1);
	    }
	    $("._year_kwh_own_consuption").html(Math.round(results[c]["kwh_savings"]["year"]));
	    year_euro_own_consuption = results[c]["kwh_savings"]["year"] * 0.200;
	    $("._year_euro_own_consuption").html(Math.round(year_euro_own_consuption));
	    $("._year_kwh_feed_in").html(Math.round(results[c]["kwh_feed_in"]["year"]));
	    year_euro_feed_in = results[c]["kwh_feed_in"]["year"] * 0.1151;
	    $("._year_euro_feed_in").html(Math.round(year_euro_feed_in));
	    $("._year_euro_sum").html(Math.round(year_euro_feed_in + year_euro_own_consuption));
	    $("._year_co2").html(Math.round(results[c]["kwh_savings"]["year"] * 0.46));


	    a = $("#overview_table tbody tr").first().attr("id","").html();
	    a = a.replace("display: none;", "");
	    a = a.replace("_autarky_", Math.round(parseFloat(results[c]["autarky"])*100, -2));
	    a = a.replace("_own_consumption_", Math.round(parseFloat(results[c]["own_consumption"])*100, -2));
	    a = a.replace("_load_profile_", $("input[name='load_profile']:checked:enabled").attr("value"));
	    a = a.replace("_energy_consumption_", $("input[name='energy_consumption']").val());
	    a = a.replace("_flat_tilt_", $("input[name='flat_tilt']").val());
	    a = a.replace("_flat_aspect_", $("input[name='flat_aspect']").val());
	    a = a.replace("_plant_kwp_", $("input[name='plant_kwp']").val());
	    a = a.replace("_yearly_profit_", Math.round(year_euro_feed_in + year_euro_own_consuption));
	    a = a.replace("_nr_", c);

	    $('#overview_table tbody').append("<tr>"+a+"</tr>").show();
	    console.log(a);
	    // scrollto("results");




	}


	var mymap = L.map('map').setView([52.402958, 12.506151], 17);

	L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v9/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibGNlbWFuIiwiYSI6ImNqamZsbG5iMzAzcmgza2w2N2RtN3ZpYWcifQ.dG7i4uKfNvbAzWzOG3g31A', {
		maxZoom: 18,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
			'<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		id: 'mapbox.streets'
	}).addTo(mymap);


	// create the tile layer with correct attribution
	// L.tileLayer( 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	//     attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
	//     subdomains: ['a','b','c']
	// }).addTo( mymap );

	var marker = L.marker([52.402958, 12.506151])
	marker.addTo(mymap);
	mymap.on('click', onMapClick);

	function onMapClick(e) {
	    marker.setLatLng(e.latlng); 

	    $("#argument_form input[name='lat']").attr("value", e.latlng.lat);
	    $("#argument_form input[name='lon']").attr("value", e.latlng.lng);
	}


	function scrollto(id){
		$("html, body").animate({ scrollTop: $("#"+id).offset().top }, 1000);
	}


});



