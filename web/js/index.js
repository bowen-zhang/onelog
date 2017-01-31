app = angular.module('OneLog', ['ngRoute']);

app.config(function($interpolateProvider, $routeProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

app.controller('SearchController', function($scope, $http, $sce) {

    $scope.search = function() {
        $http.get('/api/search', {
            params: { query: $scope.query || '' }
        }).success(function(answer) {
            console.log(answer);
            $scope.short_answer = $sce.trustAsHtml(answer.short_answer);
            $scope.full_answer = $sce.trustAsHtml(answer.full_answer);
            $scope.details = $sce.trustAsHtml(answer.details);
        });
    };
});

/*
let _logs = null;

function OneLogApp() {

    // Initialize Firebase
    const config = {
        apiKey: "AIzaSyAIBQALpCmZrVfxtdLGRVg_6guTGT2KAfw",
        authDomain: "onelog-46845.firebaseapp.com",
        databaseURL: "https://onelog-46845.firebaseio.com",
        storageBucket: "onelog-46845.appspot.com",
        messagingSenderId: "221150706298"
    };

    firebase.initializeApp(config);

    const auth = firebase.auth();
    let database = null;
    let logsRef = null;
    let queriesRef = null;
    let logs = [];
    let queries = {};

    let usernameElement = document.getElementById("Username");
    let signInButton = document.getElementById("signin");
    let profilePhotoElement = document.getElementById("ProfilePhoto");
    let groupNameField = document.getElementById("GroupName");
    let dashboardBlock = document.getElementById("Dashboard");
    let resultElement = document.getElementById("Result");
    let addQueryButton = document.getElementById("AddQuery");
    let saveQueryDialog = document.getElementById("SaveQueryDialog");

    signInButton.addEventListener("click", signIn);
    document.getElementById("Query").addEventListener("click", onQuery);
    document.getElementById("AddQuery").addEventListener("click", addQuery);
    document.getElementById("SaveQuery").addEventListener("click", saveQuery);
    queryTextElement.addEventListener("keyup", function(event) {
        event.preventDefault();
        if (event.keyCode == 13) {
            document.getElementById("Query").click();
        }
    });

    firebase.auth().onAuthStateChanged(function(user) {
      if (user) {
          signInButton.style.display = "none";
          profilePhotoElement.src = user.photoURL;
          usernameElement.innerText = user.displayName;
        load();
      }
    });

    function signIn() {
        var provider = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider).then(function(result) {
          // This gives you a Google Access Token. You can use it to access the Google API.
          var token = result.credential.accessToken;
          // The signed-in user info.
          var user = result.user;
          // ...
        }).catch(function(error) {
          // Handle Errors here.
          var errorCode = error.code;
          var errorMessage = error.message;
          // The email of the user's account used.
          var email = error.email;
          // The firebase.auth.AuthCredential type that was used.
          var credential = error.credential;
          // ...
        });
    }

    function load() {
        _logs = logs;

        database = firebase.database();
        logsRef = database.ref("logs");
        queriesRef = database.ref("queries");

        logsRef.orderByChild("TimeOut").on("child_added", function(data) {
            logs.push(data.val());
            requestDashboardRefresh();
        });

        queriesRef.on("child_added", function(data) {
            queries[data.key] = data.val();
            requestDashboardRefresh();
        });
    }

    let dashboardRefreshTimer = null;
    function requestDashboardRefresh() {
        if (dashboardRefreshTimer) {
            clearTimeout(dashboardRefreshTimer);
        }

        dashboardRefreshTimer = setTimeout(refreshDashboard, 500);
    }

    function refreshDashboard() {
        dashboardBlock.innerHTML = "";

        for (let key in queries) {
            query = queries[key];
            let result = search(query.query);
            let queryListElement = dashboardBlock.querySelector("#QueryGroup_" + query.group + " ul");
            if (!queryListElement) {
                let groupElement = document.createElement("li");
                groupElement.id = "QueryGroup_" + query.group;
                groupElement.innerHTML = `
                    <div class="GroupTitle">${query.group}</div>
                    <div class="GroupContent"><ul></ul></div>`;
                dashboardBlock.appendChild(groupElement);
                queryListElement = dashboardBlock.querySelector("#QueryGroup_" + query.group + " ul");
            }

            let queryElement = document.createElement("li");
            queryElement.innerHTML = `
                <div class="mdl-card mdl-shadow--2dp">
                    <div class="mdl-card__title">
                        <h2>${result.title}</h2>
                    </div>
                    <div class="mdl-card__supporting-text">
                        ${result.answer}
                    </div>
                    <div class="mdl-card__menu">
                        <button class="mdl-button mdl-button--icon mdl-js-button mdl-js-ripple-effect">
                            <i class="material-icons">delete</i>
                        </button>
                    </div>
                </div>`;
            queryListElement.appendChild(queryElement);
            queryElement.querySelector("button").addEventListener("click", function() {
                queriesRef.child(key).remove(function() {
                    queryElement.remove();
                });
            });
        }
    }

    const logEntryTemplate = log => html`
        <div class="Row">
            <div class="Column">${new Date(log.outTime).getMonth()}/${new Date(log.outTime).getDate()}</div>
            <div class="Column"></div>
            <div class="Column">${log.tailNumber}</div>
            <div class="Column">${log.departureAirport}</div>
            <div class="Column">${log.arrivalAirport}</div>
            <div class="Column"><div class="Remarks">${log.remarks}</div></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column"></div>
            <div class="Column">${log.totalTime}</div>
        </div>`;
    const logEntriesTemplate = logs => html`
        <div class="Table">
            <div class="HeaderRow">
                <div class="Column">YEAR
                    <br/>DATE</div>
                <div class="Column">ACFT MAKE &amp; MODEL</div>
                <div class="Column">ACFT IDENT.</div>
                <div class="Column">FROM</div>
                <div class="Column">TO</div>
                <div class="Column">REMARKS, PROCEDURES, MANEUVERS</div>
                <div class="Column">NO. INSTR. APP.</div>
                <div class="Column">NO. LDG.</div>
                <div class="Column">COMPLEX</div>
                <div class="Column">AIRPLANE SEL</div>
                <div class="Column">AIRPLANE MEL</div>
                <div class="Column">CROSS COUNTRY</div>
                <div class="Column">DAY</div>
                <div class="Column">NIGHT</div>
                <div class="Column">ACTUAL INSTR.</div>
                <div class="Column">SIMULATED INSTR.</div>
                <div class="Column">GROUND TRAINER</div>
                <div class="Column">DUAL RECEIVED</div>
                <div class="Column">PILOT IN COMMAND</div>
                <div class="Column">SOLO</div>
                <div class="Column">TOTAL DURATION OF FLIGHT</div>
            </div>
            ${logs.map(log => logEntryTemplate(log))}
        </div>`;

    var qa = {
        "(?:show me|what are) my flights on (n[0-9a-z]{5})\.?" : {
            title: (tailnumber) => `Flights on ${tailnumber.toUpperCase()}`,
            querier: (logs, tailnumber) => {
                return logs.filter(x => x.tailNumber.toLowerCase() == tailnumber);
            },
            answerTemplate: (logs) => {
                return logEntriesTemplate(logs);
            }
        },
        "what is my total time\??": {
            title: "Total Time",
            aggregator: function(log) { return log.totalTime; },
            postProcessor: (result) => result.toFixed(1),
            answerTemplate: "You have {result} hours of total time."
        },
        "(?:show me|what is) my last flight\??": {
            title: "Last Flight",
            querier: function(logs) {
                return logs.sort((a,b) => b.inTime - a.inTime)[0];
            },
            answerTemplate: function(log) {
                return `<div>From: ${log.departureAirport}</div>
                    <div>To: ${log.arrivalAirport}</div>
                    <div>Total Time: ${log.totalTime}</div>`;
            }
        },
        "until when can i take passengers\??": {
            title: "Recency for Taking Passengers",
            querier: function(logs) {
                logs = logs.filter(x => x.dayLandings > 0 || x.nightLandings > 0);
                logs = logs.sort((a,b) => b.inTime - a.inTime);
                var total = 0;
                for (var i = 0; i < logs.length; ++i) {
                    total += logs[i].dayLandings + logs[i].nightLandings;
                    if (total >= 3) {
                        var result = new Date(logs[i].inTime.valueOf());
                        result.setDate(result.getDate() + 90);
                        return result;
                    }
                }
            },
            postProcessor: (result) => moment(result).format("MMM Do, YYYY"),
            answerTemplate: "You are current to take passengers until {result}."
        }
    };

    function processQuery(q) {
        q = q.toLowerCase();
        q = q.trim();
        q = q.replace(/what's/, "what is");
        if (!q.endsWith("?")) {
            q += "?";
        }
        return q;
    }

    function onQuery() {
        let q = queryTextElement.value;
        let result = search(q);

        if (result) {
            resultElement.innerHTML = result.answer;
            addQueryButton.style.display = "inline";
        } else {
            resultElement.innerHTML = "Sorry, I don't know."
            addQueryButton.style.display = "none";
        }
    }

    function search(q) {
        q = processQuery(q);
        let match = null;
        let a = null;
        for(let key in qa) {
            if (match = q.match(key)) {
                console.log(`Found matching answer: ${key}.`);
                a = qa[key];
                break;
            }
        }

        if (!match) {
            return null;
        }

        const parameters = match.slice(1);
        console.log(`Parameters = ${parameters}`);

        let title = null;
        if (typeof a.title == "string") {
            title = a.title;
        } else if (typeof a.title == "function") {
            title = a.title.apply(null, parameters);
        }

        console.log(`Title=${title}.`);

        let result = null;
        if (a.aggregator) {
            logs.forEach((log) => result += a.aggregator(log));
        } else if (a.querier) {
            result = a.querier.apply(null, [logs].concat(parameters));
        }

        if (a.postProcessor) {
            result = a.postProcessor(result);
        }

        console.log(`Result=${result}`);

        let answer = null;
        if (typeof a.answerTemplate === "string") {
            answer = a.answerTemplate.replace('{result}', result);
        } else if (typeof a.answerTemplate === "function") {
            answer = a.answerTemplate.apply(null, [result].concat(parameters));
        }

        return {
            title: title,
            answer: answer
        };
    }

    function addQuery() {
        SaveQueryDialog.showModal();
    }

    function saveQuery() {
        queriesRef.push({
            user: firebase.auth().currentUser.uid,
            query: queryTextElement.value,
            group: groupNameField.value,
        });
        SaveQueryDialog.close();
        return false;
    }
}

window.onload = function() {
    window.app = new OneLogApp();
};

*/
