angular.module('ExampleApp', [
      'ui.bootstrap',
      'ngRoute',
      'RedhawkServices'
  ])
  .config(['$routeProvider', 
    function ($routeProvider) {
        $routeProvider
            .when('/example', {
                templateUrl: 'views/example.html',
                controller: 'ExampleController'
            })
            .otherwise({ redirectTo: '/example' });
    }
  ])
  .controller('ExampleController', ['$scope', 'user', 'Redhawk', 
    function($scope, user, Redhawk) {
      // Attach to to the first redhawk domain ID found, create and assign it to
      // a property on $scope to make it accessible from the views/example.html
      $scope.user = user;
      $scope.$watch('user.domain', function(domainId) {
        if (domainId) {
          $scope.domain = Redhawk.getDomain(domainId);
        }
      });

      $scope.$watch('domain.events.messages', function (messages) {
        $scope.messages = messages;
      })
    }
  ])
;