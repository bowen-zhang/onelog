var journey = new Vue({
    el: '#journey',
    data: {
        departureAirport: {},
        arrivalAirport: {},
        dump: ''
    },

    created: function() {
        this.$http.get('/api/log_entry_field_type').then(response => {
                data = response.body;
                this.field_types = {};
                data.forEach(x => {
                    this.field_types[x.id] = x;
                });
            })
            .then(() => {
                return this.$http.get('/api/log_entry');
            })
            .then(response => {
                this.log = response.body[0];
                let msg = '';
                for (field of this.log.data_fields) {
                    field_type = this.field_types[field.type_id.toString()];
                    if (field_type.data_type === 'TIMEDELTA') {
                        this.log[field_type.name] = (field.raw_value / 3600.0).toFixed(1);
                    } else {
                        this.log[field_type.name] = field.raw_value;
                    }
                    msg += `${field_type.name}: ${this.log[field_type.name]}\n`;
                }
                this.departureAirport = {
                    code: this.log.DepartureAirport
                };
                this.arrivalAirport = {
                    code: this.log.ArrivalAirport
                };
                this.dump = msg;
            })
            .then(() => {
                console.log('Loading flight data...');
                return this.$http.get('/api/flightdata');
            })
            .then(response => {
                console.log('Rendering flight data...');
                gpsData = response.body;

                timeline = document.getElementById('timeline');
                timeline.min = gpsData[0][0];
                timeline.max = gpsData[gpsData.length-1][0];
                timeline.MaterialSlider.change(timeline.min);


                let path = [];
                let minLat = 90, maxLat = -90;
                let minLon = 180, maxLon = -180;
                gpsData.forEach(x => {
                    path.push({ lat: x[1], lng: x[2] });
                    minLat = Math.min(minLat, x[1]);
                    maxLat = Math.max(maxLat, x[1]);
                    minLon = Math.min(minLon, x[2]);
                    maxLon = Math.max(maxLon, x[2]);
                });
                let flightPath = new google.maps.Polyline({
                    path: path,
                    geodesic: true,
                    strokeColor: '#FF0000',
                    strokeOpacity: 1.0,
                    strokeWeight: 2
                });
                flightPath.setMap(map);
                //map.setCenter({lat: gpsData[0][0], lng: gpsData[0][1]});
                map.fitBounds(new google.maps.LatLngBounds({lat: minLat, lng: minLon}, {lat:maxLat, lng:maxLon}));

                timeline.addEventListener('input', function() {
                  let path = [];
                  time = parseFloat(timeline.value);
                  gpsData.forEach(x => {
                    if (x[0] > time && x[0] < time + 600) {
                      path.push({ lat: x[1], lng: x[2] });
                    }
                  });
                  flightPath.setPath(path);
                });
            });
    }
});

var map = null;

function initMap() {
    uluru = { lat: -25.363, lng: 131.044 };
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 4,
        center: uluru
    });
}
