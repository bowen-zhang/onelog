app = angular.module('App', [])

app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

app.controller('LogEntryController', function($scope, $http) {

    $http.get('/api/log_entry_field_type').success(function(data) {
        field_types = {};
        for (type of data) {
            field_types[type.id] = type;
        }
        $scope.field_types = field_types;

        $http.get('/api/log_entry').success(function(data) {
            $scope.aircrafts = {}
            logs = Array();
            for (log of data) {
                flatLog(log);
                tail_number = $scope.get(log, 'TailNumber', null);
                if (tail_number != null && !(tail_number in $scope.aircrafts)) {
                    $scope.aircrafts[tail_number] = {};
                    get_aircraft_data(tail_number);
                }
                logs.push(log);
            }
            $scope.logs = logs
        });
    });

    function flatLog(log) {
        for (field of log.data_fields) {
            field_type = $scope.field_types[field.type_id.toString()];
            log[field_type.name] = field;
        }
    }

    function get_aircraft_data(tail_number) {
        $http.get('/api/aircraft/' + tail_number).success(function(data) {
            $scope.aircrafts[tail_number] = data;
        });
    }

    $scope.get = function(log_entry, field_name, default_value = '', converter = null) {
        value = default_value;
        if (field_name in log_entry) {
            value = log_entry[field_name].raw_value;
            if (converter != null) {
                value = converter(value);
            }
        }

        return value;
    };

    $scope.get_date = function(log_entry) {
        return $scope.get(log_entry, 'TimeIn', null, function(x) {
            return x.substring(4, 6) + '/' + x.substring(6, 8);
        });
    };

    $scope.get_approach_count = function(log_entry) {
        return $scope.get(log_entry, 'Approaches', null, function(x) {
            return eval(x).length;
        });
    }

    $scope.get_hours = function(log_entry, field_name) {
        return $scope.get(log_entry, field_name, null, function(x) {
            value = parseFloat(x) / 3600.0;
            return value;
        });
    }

    $scope.hour_formatter = function(value) {
        if (value == null || value == '') {
            return ''
        }
        return value.toFixed(1);
    }

    $scope.sum = function(func, args = []) {
        total = 0;
        func_args = args.slice();
        func_args.unshift('');
        for (log_entry of $scope.logs) {
            func_args[0] = log_entry;
            value = func.apply(null, func_args);
            if (value != null) {
                total += value;
            }
        }

        return $scope.hide_zero(total);
    }

    $scope.number_formatter = function(value) {
        if (value == null || value == '') {
            return '';
        }
        return Number.parseInt(value);
    }

    $scope.hide_zero = function(value) {
        if (value == '0' || value == 0) {
            return '';
        }
        return value;
    }
});
