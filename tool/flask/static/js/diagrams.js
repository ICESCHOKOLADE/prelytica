
function show_hour_diagram(month) {

	chart = Highcharts.chart('diagram_container', {
	    chart: {
	        type: 'line'
	    },
	    title: {
	        text: ''
	    },
	    subtitle: {
	        text: ''
	    },
	    xAxis: {
	        categories: Object.keys(kwh_yield_hour[1])
	    },
	    yAxis: {
	        title: {
	            text: 'kWh'
	        }
	    },
	    tooltip: {
	        shared: true,
	        crosshairs: true
	    },	    
	    plotOptions: {
	        line: {
	            dataLabels: {
	                enabled: false
	            },
	            enableMouseTracking: true
	        }
	    },
	    series: [],
	    credits: {
	        enabled: false
	    }
	});
}


function add_to_diagram(data, title){
	chart.addSeries({                        
	    name: title,
	    data: Object.values(data)
	});

}


function reset_diagram(){

	for(var i = chart.series.length - 1; i >= 0; i--) {
	    chart.series[i].remove(false);
	}
	chart.redraw();

}