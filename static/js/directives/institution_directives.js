(function() {
  'use strict';
  
  var module = angular.module('communityshare.directives.institutions', [
    'communityshare.services.user'
  ]);

  module.directive(
    'csInstitutions',
     function(Session, Institution) {
       return {
         scope: {
           user: '=',
           isEducator: '=',
           isCommunityPartner: '='
         },
         templateUrl: './static/templates/institution_adder.html',
         controller: function($scope) {
           $scope.updateInstitutions = function() {
             if ($scope.noInstitutions) {
               $scope.user.institution_associations = [];
               $scope.user.addNewInstitutionAssociation();
             }
           };
           // FIXME: Not scaleable.  Change to get the most popular.
           var institutionsPromise = Institution.get_many();
           var institutionTypes = [];
           $scope.options = {institutions: [],
                             institutionTypes: [],
                            };
           if ($scope.isCommunityPartner) {
             $scope.options.institutionTypes = [
               'Corporation', 'Freelancer', 'Nonprofit', 'Academic',
               'Government', 'Other'
               ];
             $scope.options.roles = [];
           } else if ($scope.isEducator) {
             $scope.options.institutionTypes = [
               'Public District School',
               'Public Charter',
               'Private School',
               'Home School',
               'Higher Education',
               'Nonprofit',
               'After School Program',
               'Other',
             ];
            $scope.options.roles = [
              'Classroom teacher',
              'Curriculum Coordinator',
              'Administator',
              'Parent',
              'Other',
            ];
           }
           if ($scope.user.institution_associations.length === 0) {
             $scope.user.institution_associations.push({});
           }
           institutionsPromise.then(
             function(institutions) {
               $scope.options.institutions = institutions;
             });
         }
       };
     });

  module.directive(
    'csInstitutionAssociationEdit',
    function() {
      return {
        scope: {
          institutionAssociation: '=',
          institutions: '=',
          institutionTypes: '=',
          roles: '=',
          disabled: '=',
          methods: '=',
          index: '@'
        },
        templateUrl: 'static/templates/institution_association.html',
      };
    });
  
})();
