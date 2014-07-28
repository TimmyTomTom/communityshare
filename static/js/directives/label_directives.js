(function() {
  'use strict';
  
  var module = angular.module('communityshare.directives.labels', [
    'communityshare.services.search'
  ]);

  module.directive(
    'csNewLabel',
     function(Session) {
       return {
         scope: {
           methods: '='
         },
         controller: function($scope) {
           $scope.update = function() {
             if ($scope.methods.onUpdate) {
               $scope.methods.onUpdate();
             }
           };
         },
         link: function(scope, elm, attrs) {
           elm.bind('keydown', function(event) {
             var ENTERCODE = 13;
             var TABCODE = 9;
             if ((event.keyCode === ENTERCODE) || (event.keyCode === TABCODE)) {
               scope.$apply(scope.update);
             }
           });
         }
       };
     });

  var LabelsController = function($scope, getAllLabels) {
    $scope.labelClasses = {
      'gradeLevels': 'light-yellow-button',
      'educatorSubjectAreas': 'light-green-button',
      'engagementLevels': 'light-blue-button'
    }
    $scope.labelInfos = [];
    for (var i=0; i<$scope.labelTitles.length; i++) {
      $scope.labelInfos.push([$scope.labelTitles[i], $scope.labelTypes[i]]);
    }
    $scope.newLabel = {
      name: ''
    };
    var labelsPromise = getAllLabels();
    labelsPromise.then(
      function(labels) {
        $scope.allLabels = labels;
      });
    $scope.typeaheadSelect = function() {
      $scope.newLabelMethods.onUpdate();
    };
    $scope.newLabelMethods = {
      onUpdate: function() {
        var newLabelName = $scope.newLabel.name;
        if (newLabelName) {
          $scope.search.displayLabelsAll.subjectAreas.Custom.push(newLabelName);
          $scope.search.activeLabels[newLabelName] = true;
        }
        $scope.search.updateNActiveLabels();
        $scope.newLabel.name = '';
      }
    };
    $scope.toggleLabel = function(label) {
      if ($scope.search.activeLabels[label]) {
        $scope.search.activeLabels[label] = false;
      } else {
        $scope.search.activeLabels[label] = true;
      }
      $scope.search.updateNActiveLabels();
    };
  };

  module.directive(
    'csLabels',
    function(Session) {
      return {
        scope: {
          search: '=',
          labelTitles: '=',
          labelTypes: '='
        },
        templateUrl: './static/templates/labels.html',
        controller: LabelsController,
      };
    });

})();
