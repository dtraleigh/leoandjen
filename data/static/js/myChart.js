var randomScalingFactor = function() {
    return Math.round(Math.random() * 100);
};

var config = {
    data: chart_data,
    options: {
        responsive: true,
        title: {
            display: false,
            text: ""
        },
        plugins:{
            legend: {
                labels: {
                    filter: function(item, chart) {
                      return !item.text.includes('none');
                    }
                }
            },
        }
    }
};

window.onload = function() {
    var chart = document.getElementById("chart").getContext("2d");
    window.myLine = new Chart(chart, config);
}
