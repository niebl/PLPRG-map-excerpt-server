var map = L.map('map').setView([51.963, 7.611], 13);
//const host = "localhost:8088"

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


async function onMapClick(e) {

    console.log(e.latlng);

    document.getElementById("lat").value = e.latlng.lat;
    document.getElementById("lon").value = e.latlng.lng;
    response = await makeQuery()

    document.getElementById("output").value = response;
    addDataToMap(response)
}


async function makeQuery(){
    resource = document.getElementById("resource").value || "reverse.php";
    host = document.getElementById("host").value
    console.log(resource)

    lat = document.getElementById("lat").value
    lon = document.getElementById("lon").value

    span=""
    if(resource == "cacheArea"){
        span = `&span=${document.getElementById("span").value}`
    }
    format=""
    if(resource == "reverse.php"){
        format = "&format=json"
    }

    //query = `http://${host}/${resource}?format=json&polygon_geojson=1&lat=${lat}&lon=${lon}${span}`
    query = `http://${host}/${resource}?lat=${lat}&lon=${lon}${span}${format}`
    
    console.log(query)

    var response = await fetch(query);
    var responseText = await response.text()

    console.log(response)
    console.log(responseText)

    return responseText;

}

function addDataToMap(geojson){
    data = JSON.parse(geojson)
    L.geoJSON(data).addTo(map);
}


map.on('click', onMapClick);