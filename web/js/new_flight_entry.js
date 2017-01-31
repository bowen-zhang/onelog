app = angular.module('OneLogApp', []);

app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

let groups = [
  {
    title: 'FLIGHT',
    fields: [
      {
          name: 'Date'
      },
      {
          name: 'TailNumber'
      },
      {
          name: 'DepartureAirport'
      },
      {
          name: 'Route'
      },
      {
          name: 'ArrivalAirport'
      },
      {
          name: 'TimeOut'
      },
      {
          name: 'TimeIn'
      }
    ]
  },
  {
    title: 'TIME',
    fields: [
      {
          name: 'TotalTime'
      },
      {
          name: 'SoloTime'
      },
      {
          name: 'ActualInstrumentTime'
      },
      {
          name: 'SimulatedInstrumentTime'
      },
      {
          name: 'NightTime'
      },
      {
          name: 'DayTime'
      },
      {
          name: 'DualReceivedTime'
      },
      {
          name: 'DualGivenTime'
      }
    ]
  },
  {
    title: 'LANDING',
    fields: [
      {
          name: 'DayLanding'
      },
      {
          name: 'NightLanding'
      }
    ]
  },
  {
    title: 'IFR',
    fields: [
      {
          name: 'Holds'
      },
      {
          name: 'Approaches'
      }
    ]
  },
  {
    title: 'MISC',
    fields: [
      {
          name: 'Remarks'
      },
      {
          name: 'FlightReview'
      }
    ]
  }
];


app.controller('FlightLogEntryController', function($scope, $http) {

    $http.get('/api/log_entry_field_type').success(function(data) {
        let idFieldMap = {};
        for (type of data) {
            idFieldMap[type.id] = type;
        }
        $scope.idFieldMap = idFieldMap;

        let nameFieldMap = {};
        for (type of data) {
            nameFieldMap[type.name] = type;
        }
        $scope.nameFieldMap = nameFieldMap;

        for (group of groups) {
            for (field of group.fields) {
                let field_type = nameFieldMap[field.name];
                field.id = field_type.id;
                field.type = field_type.data_type;
                field.displayName = field_type.display_name;
            }
        }
        $scope.groups = groups;
    });

    $scope.get_input_type = function(field) {
      if (field.name == 'TimeIn' || field.name == 'TimeOut') {
          return 'time';
      }

      switch(field.type) {
          case 'INTEGER':
          case 'FLOAT':
              return 'number';
          case 'SHORT_TEXT':
          case 'LONG_TEXT':
              return 'text';
          case 'DATETIME':
              return 'datetime';
          case 'DATE':
              return 'date';
          case 'TIMEDELTA':
              return 'number';
          default:
              return 'text';
      }
    };

    function padding(value, digits) {
        str = value.toString();
        while (digits > str.length) {
            str = '0' + str;
        }
        return str;
    }

    $scope.get_value = function(field) {
      if (field.name == 'TimeIn' || field.name == 'TimeOut') {
          return padding(field.value.getHours(), 2) + padding(field.value.getMinutes(), 2) + padding(field.value.getSeconds(), 2);
      }

      switch(field.type) {
          case 'INTEGER':
          case 'FLOAT':
              return field.value.toString();
          case 'SHORT_TEXT':
          case 'LONG_TEXT':
              return field.value;
          case 'DATETIME':
              return null;
          case 'DATE':
              return padding(field.value.getFullYear(), 4) + padding(field.value.getMonth()+1, 2) + padding(field.value.getDate(), 2);
          case 'TIMEDELTA':
              return (field.value*3600).toString();
          default:
              return field.value;
      }
    }

    $scope.save = function() {
        let log = {
            data_fields: []
        };
        for (group of $scope.groups) {
            for (field of group.fields) {
                if (field.value) {
                    log.data_fields.push({
                        airman_id: 4899861,
                        type_id: field.id,
                        raw_value: $scope.get_value(field)
                    });
                }
            }
        }
        $http.post('/api/log_entry', log).success(function(data) {
            alert('Saved!');
        });

        return false;
    };
});

