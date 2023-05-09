//*** Create the Map
// Map start
var map = L.map('map', {fullscreenControl: true}).setView([37.8, -96], 3);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiY29waGVhZDU2NyIsImEiOiJjanF2MGdtNmYwcWJ3NDhtbGUxa3U0ZjZhIn0.V1sXYuvUf6MeTSMZVOS84g', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
        '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1
}).addTo(map);

L.geoJson(statesData).addTo(map);
//*** Map create end

//*** Control elements
var info = L.control();

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};

// method that we will use to update the control based on feature properties passed
info.update = function (props) {
    this._div.innerHTML = (props ? '<b>' + props.name + '</b><br />'
        : 'Hover over a state');
};

info.addTo(map);
//*** end control

//*** Stuff that happens when you hover a mouse over the state
// Mouse in
function highlightFeature(e) {
    var layer = e.target;

    layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }

    info.update(layer.feature.properties);
}

var geojson;

// Mouse out
function resetHighlight(e) {
    geojson.resetStyle(e.target);
    info.update();
}

function zoomToFeature(e) {
    map.fitBounds(e.target.getBounds());
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
    });
}

//*** Create the states outline and colors, styles

// Return a fillcolor if the state has been visited
function getColor(n) {
    var color;
    var visited = visited_states.includes(n);

    if (visited){
        color = "#46AA14";
    } else {
        color = "#DDDDDD";
    }
    return color;
}

// state styles
function getStyle(feature) {
    return {
        fillColor: getColor(feature.properties.name),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

L.geoJson(statesData, {style: getStyle}).addTo(map);

geojson = L.geoJson(statesData, {
    style: getStyle,
    onEachFeature: onEachFeature
}).addTo(map);

//*** Let's add US capital cities
var awesomeMarker;
var capital_popup = "Capital Name";

for (var city in cities) {
    if (us_visited_cities.includes(cities[city].city_name) == true){
        capital_popup = cities[city].city_name + ', ' + cities[city].state_code + " [<a href=\"/capitals/capital/" + cities[city].city_name + "\">📸</a>]"
    } else {
        capital_popup = cities[city].city_name + ', ' + cities[city].state_code
    }
    L.marker(
        [cities[city].latitude, cities[city].longitude],
        {
            // icon: awesomeMarker,
            icon: L.AwesomeMarkers.icon({icon: 'star', prefix: 'fa', markerColor: 'cadetblue', iconColor: '#fff'}),
            riseOnHover: true,
            title: cities[city].city_name + ', ' + cities[city].state_code
        }
    )
    .addTo(map)
    .bindPopup(capital_popup);

}

for (var capital in country_capitals) {
    L.marker(
        [country_capitals[capital].fields.lat, country_capitals[capital].fields.lon],
        {
            // icon: awesomeMarker,
            icon: L.AwesomeMarkers.icon({icon: 'star', prefix: 'fa', markerColor: 'red', iconColor: '#fff'}),
            riseOnHover: true,
            title: country_capitals[capital].fields.name
        }
    )
    .addTo(map)
    .bindPopup(country_capitals[capital].fields.name + " [<a href=\"/capitals/capital/" + country_capitals[capital].fields.name + "\">📸</a>]");

}