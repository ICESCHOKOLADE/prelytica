var kwh_yield_hour;
var results = {};
var chart;
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

	c = 0;
	$("#argument_form").submit(function(e){
		$("#ajax_loader").show();
	    $.ajax({
	           type: "GET",
	           url: "tool_request",
	           data: $("#argument_form").serialize(),
	           dataType: "json",
	           async:true,  
	           success: function(data){
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


	           }
	         });
	    e.preventDefault(); 
	});




	$("#add_diagram_form").submit(function(e){
		e.preventDefault();
		data_type = $('#data_type option:selected').val();
		month = $('#month option:selected').val();
		result_nr = $('#result_nr option:selected').val();
		data = results[result_nr][data_type][month];
		console.log(results[result_nr]["autarky"]);
		if (data_type=="kwh_yield") {
			data = results[result_nr][data_type]["hour"][month];
		}
		title = month_word[month]+"_"+data_type ;
		// console.log(data);
		add_to_diagram(data, title);
	});

	$("#reset_diagram").click(function(){
		reset_diagram();
	});


	function handle_result_data(c) {
	    kwh_yield_hour = results[c]["kwh_yield"]["hour"];
	    show_hour_diagram(2);
	    $("._year_kwh_own_consuption").html(Math.round(results[c]["kwh_savings"]["year"]));
	    year_euro_own_consuption = results[c]["kwh_savings"]["year"] * 0.200;
	    $("._year_euro_own_consuption").html(Math.round(year_euro_own_consuption));
	    $("._year_kwh_feed_in").html(Math.round(results[c]["kwh_feed_in"]["year"]));
	    year_euro_feed_in = results[c]["kwh_feed_in"]["year"] * 0.1151;
	    $("._year_euro_feed_in").html(Math.round(year_euro_feed_in));
	    $("._year_euro_sum").html(Math.round(year_euro_feed_in + year_euro_own_consuption));
	    
	    a = $("#overview_table tbody tr").first().attr("id","").html();
	    a = a.replace("display: none;", "");
	    a = a.replace("_autarky_", Math.round(parseFloat(results[c]["autarky"])*100, -2));
	    a = a.replace("_own_consumption_", Math.round(parseFloat(results[c]["own_consumption"])*100, -2));
	    a = a.replace("_load_profile_", $("input[name='load_profile']:checked:enabled").attr("value"));
	    a = a.replace("_energy_consumption_", $("input[name='energy_consumption']").val());
	    a = a.replace("_plant_kwp_", $("input[name='plant_kwp']").val());
	    a = a.replace("_yearly_profit_", Math.round(year_euro_feed_in + year_euro_own_consuption));
	    a = a.replace("_nr_", c);

	    $('#overview_table tbody').append("<tr>"+a+"</tr>").show();
	    console.log(a);




	}




});



