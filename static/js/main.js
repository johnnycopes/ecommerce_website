
var app = angular.module('store', ['ui.router', 'ngCookies']);

app.config(function($stateProvider, $urlRouterProvider) {
  $stateProvider
  .state({
      name: 'checkout',
      url: '/checkout',
      templateUrl: 'templates/checkout.html',
      controller: 'CheckoutController'
    })
    .state({
      name: 'home',
      url: '/',
      templateUrl: 'templates/home.html',
      controller: 'MainController'
    })
    .state({
      name: 'login',
      url: '/login',
      templateUrl: 'templates/login.html',
      controller: 'LoginController'
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
      name: 'thanks',
      url: '/thanks',
      templateUrl: 'templates/thanks.html'
    })
    .state({
      name: 'view_cart',
      url: '/view_cart',
      templateUrl: 'templates/view_cart.html',
      controller: 'CartController'
    });

  $urlRouterProvider.otherwise('/');
});

app.factory('StoreService', function($http, $cookies, $rootScope) {
  var service = {};
  // set cookie data to username or guest
  if (!$cookies.getObject('cookie_data')) {
    $rootScope.displayName = 'Guest';
    $rootScope.loggedIn = false;
  }
  else {
    var cookie = $cookies.getObject('cookie_data');
    $rootScope.displayName = cookie.username;
    $rootScope.token = cookie.token;
    $rootScope.loggedIn = true;
  }
  // logout
  $rootScope.logout = function() {
    $cookies.remove('cookie_data');
    $rootScope.displayName = 'Guest';
    $rootScope.token = null;
    $state.go('home');
  };
  service.addToCart = function(addToCartData) {
    var url = '/api/shopping_cart';
    return $http({
      method: 'POST',
      url: url,
      data: addToCartData
    });
  };
  service.checkout = function(formData) {
    var url = '/api/shopping_cart/checkout';
    return $http({
      method: 'POST',
      url: url,
      data: formData
    });
  };
  service.getDetails = function(id) {
    var url = '/api/product/' + id;
    return $http({
      method: "GET",
      url: url
    });
  };
  service.getProducts = function() {
    var url = "/api/products";
    return $http({
      method: "GET",
      url: url
    });
  };
  service.login = function(formData) {
    var url = '/api/user/login';
    return $http({
      method: 'POST',
      url: url,
      data: formData
    }).success(function(login_data) {
      $cookies.putObject('cookie_data', login_data);
      $rootScope.displayName = login_data.username;
      $rootScope.token = login_data.token;
    });;
  };
  service.signup = function(formData) {
    var url = '/api/user/signup';
    return $http({
      method: 'POST',
      url: url,
      data: formData
    });
  };
  service.viewCart = function() {
    var url = '/api/shopping_cart';
    return $http({
      method: 'GET',
      url: url,
      params: {
        token: $rootScope.token
      }
    });
  };

  return service;
});

app.controller("CartController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  StoreService.viewCart().success(function(resultsArr) {
    $scope.cart = resultsArr.product_query;
    $scope.total = resultsArr.total_price;
  });
});

app.controller("CheckoutController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $scope.checkoutSubmit = function() {
    var formData = {
      street_address: $scope.streetAddress,
      city: $scope.city,
      state: $scope.state,
      post_code: $scope.postCode,
      country: $scope.country,
      token: $rootScope.token
    };
    $scope.formSubmitted = true;
    return formData;
  };
  $scope.confirmCheckout = function() {
    StoreService.checkout($scope.checkoutSubmit()).success(function() {
      $scope.formSubmitted = false;
      $state.go('thanks');
    });
  };
});

app.controller("DetailsController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $scope.id = $stateParams.product_id;
  StoreService.getDetails($scope.id).success(function(item) {
    $scope.name = item.name;
    $scope.description = item.description;
    $scope.image = item.image_path;
    $scope.price = item.price;
  });
  $scope.addToCart = function() {
    if (!$rootScope.loggedIn) {
      $scope.rejected = true;
      $cookies.putObject('location', {product_id: $scope.id});
    }
    else {
      var addToCartData = {
        token: $rootScope.token,
        product_id: $scope.id
      };
      StoreService.addToCart(addToCartData);
      $state.go('view_cart');
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
    })
    .success(function(login_data) {
      $cookies.putObject('cookie_data', login_data);
      $state.go('home');
    });
  };
});

app.controller("MainController", function($scope, StoreService, $stateParams, $state) {
  StoreService.getProducts().success(function(results) {
    $scope.results = results;
    $scope.getItemId = function(item) {
      $scope.id = item.id;
    };
  });
});

app.controller('SignupController', function($scope, StoreService, $stateParams, $cookies, $state) {
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
