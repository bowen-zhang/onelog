Vue.component('journey', {
    props: ['log'],
    template: `
    <div>
        <div class="departure">
            <div class="airport-code">{{ departureAirport.code }}</div>
            <div class="airport-city">{{ departureAirport.city }}, {{departureAirport.state}}</div>
        </div>
        <div class="arrival">
            <div class="airport-code">{{ arrivalAirport.code }}</div>
            <div class="airport-city">{{ arrivalAirport.city }}, {{arrivalAirport.state}}</div>
        </div>
        <div><pre>{{ dump }}</pre></div>
    </div>
    `,
    data: function() {
        return {
            dump: ''
        }
    },
    computed: {
        test: function() {
            return 'helo';
        },
        departureAirport: function() {
            if (this.log) {
                return this.getAirportInfo(this.log.DepartureAirport);
            } else {
                return null;
            }
        },
        arrivalAirport: function() {
            if (this.log) {
                return this.getAirportInfo(this.log.ArrivalAirport);
            } else {
                return null;
            }
        },
    },
    methods: {
        getAirportInfo: function(code) {
            let info = { code: code };
            info.city = "[City]";
            info.state = "[State]";
            return info;
        }
    }
});

var logEntry = new Vue({
    el: '#logEntry',
    data: {
        log: null,
        dump: '',
    },

    created: function() {
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

field_types = {};
Vue.http.get('/api/log_entry_field_type').then(response => {
                data = response.body;
                data.forEach(x => {
                    this.field_types[x.id] = x;
                });
            })
            .then(() => {
                return Vue.http.get('/api/log_entry');
            })
            .then(response => {
                log = response.body[response.body.length-1];
                let msg = '';
                for (field of log.data_fields) {
                    field_type = field_types[field.type_id.toString()];
                    if (field_type.data_type === 'TIMEDELTA') {
                        log[field_type.name] = (field.raw_value / 3600.0).toFixed(1);
                    } else {
                        log[field_type.name] = field.raw_value;
                    }
                    msg += `${field_type.name}: ${log[field_type.name]}\n`;
                }
                logEntry.log = log;
                /*
                this.departureAirport = {
                    code: this.log.DepartureAirport
                };
                this.arrivalAirport = {
                    code: this.log.ArrivalAirport
                };
                */
                logEntry.dump = msg;
            })
            .then(() => {
                console.log('Loading flight data...');
                return Vue.http.get(`/api/flightdata/${logEntry.log.flight_id}`);
            })
            .then(response => {
                gpsData = response.body;

                timeline = document.getElementById('timeline');
                timeline.min = parseInt(gpsData[0][0]);
                timeline.max = parseInt(gpsData[gpsData.length-1][0]);
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
                map.fitBounds(new google.maps.LatLngBounds({lat: minLat, lng: minLon}, {lat:maxLat, lng:maxLon}));

                timeline.addEventListener('input', function() {
                  let path = [];
                  time = parseFloat(timeline.value);
                  if (time == timeline.min || time == timeline.max) {
                      gpsData.forEach(x => {
                        path.push({ lat: x[1], lng: x[2] });
                      });
                  } else {
                      gpsData.forEach(x => {
                        if (x[0] > time && x[0] < time + 120) {
                          path.push({ lat: x[1], lng: x[2] });
                        }
                      });
                  }
                  flightPath.setPath(path);
                });
            });
