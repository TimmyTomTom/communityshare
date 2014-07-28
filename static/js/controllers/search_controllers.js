(function() {
  'use strict';

  var module = angular.module(
    'communityshare.controllers.search',
    [
      'communityshare.controllers.conversation',
    ]);

  module.controller(
    'MatchesController',
    function($scope, Session, Search, $location, $modal) {
      $scope.Session = Session;
      var user = Session.activeUser;
      $scope.infoMessage = 'Loading searches...';
      $scope.errorMessage = '';
      $scope.title = '';
      $scope.goToConversation = function(conversation) {
        $location.path('/conversation/' + conversation.id);
      };

      var searchesPromise = Search.get_many({'searcher_user_id': user.id});
      searchesPromise.then(
        function(searches) {
          $scope.infoMessage = '';
          $scope.errorMessage = '';
          $scope.searches = searches;
          var compareSearchDate = function(search1, search2) {
            var output = -1;
            if (search1.created === search2.created) {
              output = 0;
            } else if (search1.created < search2.created) {
              output = 1;
            }
            return output;
          };
          $scope.searches.sort(compareSearchDate);
          if ($scope.searches.length > 0) {
            $scope.getMatches($scope.searches[0]);
          }
        },
        function() {
          console.log('failed to get searches');
        });
      $scope.getMatches = function(search) {
        var matchesPromise = Search.getResults(search.id);
        search.show = true;
        search.infoMessage = 'Loading matches...';
        search.errorMessage = '';
        matchesPromise.then(
          function(matches) {
            search.matches = matches;
            search.infoMessage = '';
            search.errorMessage = '';
          },
          function(errorMessage) {
            search.infoMessage = '';
            search.errorMessage = errorMessage;
          });
      };
      $scope.startConversation = function(userId, searchId) {
        var opts = {
          templateUrl: './static/templates/new_conversation.html',
          controller: 'NewConversationController',
          resolve: {
            userId: function() {return userId;},
            searchId: function() {return searchId;}
          }
        };
        var m = $modal.open(opts);
        m.result.then(
          function(conversation) {
            if (conversation) {
              $location.path('/conversation/' + conversation.id);
            }
          });
      };
    });

  module.controller(
    'SearchResultsController',
    function(Session, $scope, $location, $routeParams, $modal, Search, Messages) {
      $scope.Session = Session;
      var searchId = $routeParams.searchId;
      $scope.infoMessage = 'Searching for matches...';
      $scope.errorMessage = '';
      $scope.title = '';
      $scope.goToConversation = function(conversation) {
        $location.path('/conversation/' + conversation.id);
      };

      $scope.startConversation = function(userId) {
        var opts = {
          templateUrl: './static/templates/new_conversation.html',
          controller: 'NewConversationController',
          resolve: {
            userId: function() {return userId;},
            searchId: function() {return searchId;}
          }
        };
        var m = $modal.open(opts);
        m.result.then(
          function(conversation) {
            if (conversation) {
              $location.path('/conversation/' + conversation.id);
            }
          });
      };
      if (searchId !== undefined) {
        var searchesPromise = Search.getResults(searchId);
        searchesPromise.then(
          function(searches) {
            $scope.searches = searches;
            if (searches.length === 0) {
              $scope.infoMessage = 'No matches found.';
            } else {
              $scope.infoMessage = '';
              if (searches[0].searcher_role === 'educator') {
                $scope.title = 'Best Educator Matches';
              } else {
                $scope.title = 'Best Community Partner Matches';
              }
            }
            $scope.errorMessage = '';
          },
          function(message) {
            var msg = '';
            if (message) {
              msg = ': ' + message;
            }
            $scope.errorMessage = 'Failed to find matches' + msg;
          });
      }
    });      

  module.controller(
    'SearchEditController',
    function(Session, $location, $scope, $routeParams, Search, Messages) {
      var searchId = $routeParams.searchId;
      if (searchId !== undefined) {
        var searchPromise = Search.get(searchId);
        searchPromise.then(
          function(search) {
            $scope.search = search;
            $scope.search.makeLabelDisplay();
          },
          function(message) {
            Messages.error(message);
          });
      } else {
        var searcher_role;
        var searching_for_role;
        if (Session.activeUser.is_educator) {
          searcher_role = 'educator';
          searching_for_role = 'partner';
        } else {
          searcher_role = 'partner';
          searching_for_role = 'educator';
        }
        $scope.search = new Search({
          searcher_user_id: Session.activeUser.id,
          searcher_role: searcher_role,
          searching_for_role: searching_for_role,
          zipcode: Session.activeUser.zipcode
        });
        $scope.search.makeLabelDisplay();
      }

      $scope.saveSettings = function() {
        $scope.search.processLabelDisplay();
        var promise = $scope.search.save();
        promise.then(
          function(search) {
            $location.path('/matches');
          },
          function(message) {
            Messages.error(message);
          });
      };
    });
  
})();
