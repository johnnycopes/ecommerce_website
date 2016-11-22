
var app = angular.module('store', ['ui.router', 'ngCookies']);

app.config(function($stateProvider, $urlRouterProvider) {
  $stateProvider
    .state({
      name: 'home',
      url: '/',
      templateUrl: 'templates/home.html',
      controller: 'MainController'
    })
    .state({
      name: 'product_details',
      url: '/product/{product_id}',
      templateUrl: 'templates/product_details.html',
      controller: 'DetailsController'
    })
    .state({
      name: 'signup',
      url: '/signup',
      templateUrl: 'templates/signup.html',
      controller: 'SignupController'
    })
    .state({
      name: 'login',
      url: '/login',
      templateUrl: 'templates/login.html',
      controller: 'LoginController'
    });
  $urlRouterProvider.otherwise('/');
});

app.factory('StoreService', function($http, $cookies, $rootScope) {
  var service = {};
  // var cookie = $cookies.getObject('data');
  // $rootScope.username = cookie.username;
  // console.log($cookies);
  service.getProducts = function() {
    var url = "/api/products";
    return $http({
      method: "GET",
      url: url
    });
  };
  service.getDetails = function(id) {
    var url = '/api/product/' + id;
    return $http({
      method: "GET",
      url: url
    });
  };
  service.signup = function(formData) {
    var url = '/api/user/signup';
    return $http({
      method: 'POST',
      url: url,
      data: formData
    });
  };
  service.login = function(formData) {
    var url = '/api/user/login';
    return $http({
      method: 'POST',
      url: url,
      data: formData
    });
  };

  return service;
});

app.controller("MainController", function($scope, StoreService, $stateParams, $state) {
  StoreService.getProducts().success(function(results) {
    $scope.results = results;
    $scope.getItemId = function(item) {
      $scope.id = item.id;
    };
  });
});

app.controller("DetailsController", function($scope, StoreService, $stateParams, $state) {
  $scope.id = $stateParams.product_id;
  StoreService.getDetails($scope.id).success(function(item) {
    $scope.name = item.name;
    $scope.description = item.description;
    $scope.image = item.image_path;
  });
});

app.controller('SignupController', function($scope, StoreService, $stateParams, $state) {
  $scope.signupSubmit = function() {
    if ($scope.password != $scope.confirmPassword) {
      $scope.passwordsdontmatch = true;
    }
    else {
      $scope.passwordsdontmatch = false;
      var formData = {
        username: $scope.username,
        email: $scope.email,
        password: $scope.password,
        first_name: $scope.firstName,
        last_name: $scope.lastName
      };
      StoreService.signup(formData).success(function() {
        $state.go('login');
      });
    }
  };
});

app.controller("LoginController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $scope.login = function() {
    var formData = {
      username: $scope.username,
      password: $scope.password
    };
    StoreService.login(formData).error(function(){
      $scope.wronglogin = true;
    });
    StoreService.login(formData).success(function(data) {
      $cookies.putObject('data', data);
      $state.go('home');
    });
  };
});
