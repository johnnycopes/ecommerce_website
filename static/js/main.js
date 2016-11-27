
var app = angular.module('store', ['ui.router', 'ngCookies', 'ngAnimate']);

// This is the state configuration. States are views that a user will see by loading page templates and designating which controllers run those views.
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
      controller: 'HomeController'
    })
    .state({
      name: 'login',
      url: '/login',
      templateUrl: 'templates/login.html',
      controller: 'LoginController'
    })
    .state({
      name: 'products',
      url: '/products',
      templateUrl: 'templates/products.html',
      controller: 'ProductsController'
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
    })
    ;

  $urlRouterProvider.otherwise('/');
});

// This is the API. It has all the various services that can be used throughout the app. I also take care of setting rootScope variables for handling the authorization auth_tokens needed for cookies.
app.factory('StoreService', function($http, $state, $cookies, $rootScope) {
  var service = {};
  // set cookie data to username or guest
  if (!$cookies.getObject('cookie_data')) {
    $rootScope.displayName = null;
    $rootScope.loggedIn = false;
  }
  else {
    var cookie = $cookies.getObject('cookie_data');
    $rootScope.displayName = cookie.username;
    $rootScope.auth_token = cookie.auth_token;
    $rootScope.loggedIn = true;
  }
  // logout
  $rootScope.logout = function() {
    $cookies.remove('cookie_data');
    $rootScope.displayName = null;
    $rootScope.auth_token = null;
    $rootScope.loggedIn = false;
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
      $rootScope.auth_token = login_data.auth_token;
      $rootScope.loggedIn = true;
    });
  };
  service.removeFromCart = function(removeFromCartData) {
    var url = '/api/remove_product';
    return $http({
      method: 'POST',
      url: url,
      data: removeFromCartData
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
  service.viewCart = function() {
    var url = '/api/shopping_cart';
    return $http({
      method: 'GET',
      url: url,
      params: {
        auth_token: $rootScope.auth_token
      }
    });
  };
  return service;
});

// The controllers that pass information beween the model and view
app.controller("CartController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $rootScope.noSplash = true;
  StoreService.viewCart()
    .success(function(resultsArr) {
      $scope.cart = resultsArr.product_query;
      $scope.total = resultsArr.total_price;
    });
  $scope.removeFromCart = function(itemId) {
    var removeFromCartData = {
      item_id: itemId,
      auth_token: $rootScope.auth_token
    };
    StoreService.removeFromCart(removeFromCartData)
      // if remove method is successful, call the view_cart method to update the cart immediately
      .success(function(){
        StoreService.viewCart()
          .success(function(resultsArr) {
            $scope.cart = resultsArr.product_query;
            $scope.total = resultsArr.total_price;
          });
      });
  };
});

app.controller("CheckoutController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $rootScope.noSplash = false;
   // This packages up all the needed info to send to the backend upon a successful transaction.
  $scope.checkoutSubmit = function(token) {
    var formData = {
      street_address: $scope.streetAddress,
      city: $scope.city,
      state: $scope.state,
      post_code: $scope.postCode,
      country: $scope.country,
      auth_token: $rootScope.auth_token,
      stripe_token: token
    };
    $scope.formSubmitted = true;
    return formData;
  };
  // This is the final call for checking out. It opens the Stripe popup that will take care of the credit card charge. Once successful, the callback StripeHandler runs the checkout method which runs the checkoutSubmit as well, which adds info to the purchase and products_in_purchase tables and deletes the items from the products_in_shopping_cart table.
  $scope.confirmCheckout = function() {
    $scope.stripeHandler.open({
      name: 'Checkout',
      description: 'Jamón Depot',
      amount: $scope.stripeTotal
    });
  };
  StoreService.viewCart()
    .success(function(cart) {
      $scope.total = cart.total_price;
      $scope.stripeTotal = cart.total_price * 100;
    });
  // This is the Stripe handler which uses the Stripe service for payment. It uses my personal Stripe API key in order to open the Stripe service. Also, on callback of that service it runs the checkout method.
  $scope.stripeHandler = StripeCheckout.configure({
    key: 'pk_test_zs9Kch71dKtIFjsNfa12k10x',
    locale: 'auto',
    token: function callback(token) {
      var stripeToken = token.id;
      StoreService.checkout($scope.checkoutSubmit(stripeToken))
        .success(function() {
          $scope.formSubmitted = false;
          $state.go('thanks');
        })
        .error(function() {
          console.log('something went wrong');
        });
    }
  });
});

app.controller("DetailsController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $rootScope.noSplash = true;
  $scope.id = $stateParams.product_id;
  StoreService.getDetails($scope.id)
    .success(function(item) {
      $scope.name = item.name;
      $scope.description = item.description;
      $scope.image = item.image_path;
      $scope.price = item.price;
      $scope.brand = item.brand;
    })
    .error(function() {
      console.log('error!');
    });
  $scope.addToCart = function() {
    if (!$rootScope.loggedIn) {
      $state.go('signup');
    }
    else {
      var addToCartData = {
        auth_token: $rootScope.auth_token,
        product_id: $scope.id
      };
      StoreService.addToCart(addToCartData);
      $state.go('view_cart');
    }
  };
});

app.controller("HomeController", function($rootScope) {
  $rootScope.noSplash = false;
});

app.controller("LoginController", function($scope, StoreService, $stateParams, $state, $cookies, $rootScope) {
  $rootScope.noSplash = false;
  $scope.login = function() {
    var formData = {
      username: $scope.username,
      password: $scope.password
    };
    StoreService.login(formData)
      .error(function(){
        $scope.wronglogin = true;
      })
      .success(function(login_data) {
        $cookies.putObject('cookie_data', login_data);
        $state.go('home');
      });
  };
});

app.controller("ProductsController", function($scope, $rootScope, StoreService, $stateParams, $state) {
  $rootScope.noSplash = true;
  StoreService.getProducts()
    .success(function(results) {
      $scope.results = results;
      $scope.getItemId = function(item) {
        $scope.id = item.id;
      };
    });
});

app.controller('SignupController', function($scope, $rootScope, StoreService, $stateParams, $cookies, $state) {
  $rootScope.noSplash = false;
  $scope.signupSubmit = function() {
    if ($scope.password !== $scope.confirmPassword) {
      $scope.formError = true;
      $scope.errorMessage = 'Passwords don\'t match';
    }
    else {
      $scope.formError = false;
      var formData = {
        username: $scope.username,
        email: $scope.email,
        password: $scope.password,
        first_name: $scope.firstName,
        last_name: $scope.lastName
      };
      StoreService.signup(formData)
        .success(function() {
          $state.go('login');
        })
        .error(function() {
          $scope.errorMessage = 'Could not sign up';
        });
    }
  };
});

app.directive('navOffset', function(){
  var navbar = document.querySelector('nav');
      navbarHeight = navbar.offsetHeight;
  return {
    link: function(scope, element, attrs) {
      element.css('margin-top', navbarHeight + 'px');
    }
  }
});
