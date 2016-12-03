# Jamón Depot
<img src="static/img/screenshots/jamon_depot.png" alt="Jamón Depot logo" width="250px"/>
######
[Live Project](http://jamondepot.club/#/)   |   [Overview](https://github.com/johnnycopes/ecommerce_website/#overview)   |   [What I Used](https://github.com/johnnycopes/ecommerce_website#what-i-used)   |   [MVP](https://github.com/johnnycopes/ecommerce_website#mvp-minimum-viable-product)   |   [Challenges](https://github.com/johnnycopes/ecommerce_website#challenges--solutions)   |   [Code](https://github.com/johnnycopes/ecommerce_website#code-snippets)   | [Screenshots](https://github.com/johnnycopes/ecommerce_website#screenshots)   |

## Overview:

## What I used:
**Languages/Frameworks:**
* HTML5
* CSS
* Bootstrap
* PostgreSQL
* AngularJS (including the following services)
  * ui-router
  * ngCookies
  * ngAnimate
* Python/Flask (including the following modules)
  * PyGreSQL
  * bcrypt
  * dotenv
  * uuid
  * os

**Other:**
* Postman
* Stripe API
* Logo icon from [Freepik](http://www.flaticon.com/search?word=spanish%20food/)


## MVP (Minimum Viable Product):
The original assignment was to create an e-commerce website.


**Initial MVP**
* Display different products, details, and prices dynamically from database
* Customer can sign up, log in, log out, add items to the shopping cart, and check out
* Implement the Stripe API for the check out process

**Stretch Goals**
* More sophisticated form verification for check out process
* Use of geolocation to convert currency and shipping details form

## Challenges & Solutions:

1. **Challenge:** Properly setting up the structure of the application. This was the first time I'd ever made a full-stack SPA.

    **Solution:** This wasn't one specific problem in the project but rather an overarching challenge. Here, instead of just using Python and Jinja to serve up information on the client side, I had to pass it through to Angular which would in turn render everything. It took some time to get used to get used to sending requests and receiving data with so many moving parts, but I felt much more comfortable with it by the end.

2.  **Challenge:** Requiring valid login details in order to access certain pages.

    **Solution:** Upon successful login, the user is given a unique authorization token (created by the uuid module) which is then stored in a variable in the root scope (essentially the global scope of an Angular app). That way, every time the user navigates to a page where being logged in is necessary in order to see the content (e.g. the "checkout" page), the program can simply check that the saved auth token matches an existing user and if it doesn't or there isn't one, access is denied.

3.  **Challenge:** Maintaining login details even on a page refresh.

    **Solution:** A straightforward way to persist temporary data is to take advantage of cookies. Using the ngCookies service in Angular, I saved the user's authorization token in a cookie object and passed it to the browser. From there, I added some code that checks if there are any cookies associated with the page when it loads and stores them in a variable on the root scope.

4.  **Challenge:** Incorporating the Stripe API

    **Solution:** This was one of the first times I'd used a third-party API in a project, so it took some time to read through the documentation and figure out all of the steps. Fortunately, Stripe is a large company and the documentation was quite good so it was mostly a matter of following the instructions.


## Code Snippets

User log in process:
``` Python
@app.route('/api/user/login', methods=['POST'])
def login():
    user = request.get_json()
    username = user['username']
    password = user['password']
    salt = bcrypt.gensalt() # generate a salt
    encrypted_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # the following line will take the original salt that was used
    # in the generation of the encrypted password, which is stored as
    # part of the encrypted_password, and hash it with the entered password
    rehash = bcrypt.hashpw(password.encode('utf-8'), encrypted_password)
    if rehash == encrypted_password:
        auth_token = uuid.uuid4()
        user = db.query('''
        SELECT
            id, first_name
        FROM
            customer
        WHERE
            username = $1''', username).namedresult()[0]
        db.insert (
            "auth_token",
            token = auth_token,
            customer_id = user.id
        )
        login_data = {
            'auth_token': auth_token,
            'customer_id': user.id,
            'username' : user.first_name
        }
        return jsonify(login_data)
    else:
        return "Incorrect password", 401
```

Check out process (front-end):
```JavaScript
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
```

Check out process (back-end):
```Python
@app.route('/api/shopping_cart/checkout', methods=["POST"])
def checkout():
    post_token = request.get_json().get('auth_token')
    formData = request.get_json()
    customer_id = db.query('''
    SELECT
        customer.id
    FROM
        customer, auth_token
    WHERE
        customer.id = auth_token.customer_id AND
        now() < token_expires AND
        auth_token.token = $1
    ''', post_token).namedresult()
    print customer_id
    if customer_id == []:
        return 'Forbidden', 403
    else:
        customer_id = customer_id[0].id
        total_price = db.query("""
        SELECT
            sum(price)
        FROM
            product_in_shopping_cart
        INNER JOIN
            product ON product.id = product_id
        INNER JOIN
            auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
        WHERE
            auth_token.token = $1""", post_token).namedresult()[0].sum
        purchased_items = db.query("""
        SELECT
            price, product.name, product.id
        FROM
            product_in_shopping_cart
        INNER JOIN
            product ON product.id = product_id
        INNER JOIN
            auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
        WHERE
            auth_token.token = $1""", post_token).dictresult()
        purchase = db.insert('purchase', {
            'customer_id': customer_id,
            'total_price': total_price,
            'city': formData['city'],
            'street_address': formData['street_address'],
            'state': formData['state'],
            'post_code': formData['post_code'],
            'country': formData['country']
        })
        for item in purchased_items:
            db.insert('product_in_purchase', {
                'product_id': item['id'],
                'purchase_id': purchase['id']
            })
        db.query("""
            DELETE
                FROM
                    product_in_shopping_cart
                WHERE
                    customer_id = $1""", customer_id)

        # code from Stripe
        amount = total_price * 100

        stripe.Charge.create(
            amount=amount,
            currency='usd',
            source=formData['stripe_token'],
            description='Flask Charge'
        )

        return jsonify(purchase)
```

## Screenshots
![Homepage](img/screenshots/homepage.png)
![Sign up](img/screenshots/signup.png)
![View Cart](img/screenshots/viewcart.png)
![Checkout](img/screenshots/checkout.png)
![Checkout w/Stripe](img/screenshots/stripe_checkout.png)
![Tablet](img/screenshots/tablet.png)
![Phone](img/screenshots/mobile.png)

********
