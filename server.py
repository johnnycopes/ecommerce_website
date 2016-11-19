from flask import Flask, jsonify, request, redirect
import bcrypt, uuid, pg, os


db = pg.DB(dbname='ecommerce_db')
app = Flask('ecommerceApp')


@app.route('/api/products')
def products():
    results = db.query('SELECT * FROM product').dictresult()
    return jsonify(results)


@app.route('/api/products/<prod_id>')
def products_prod_id(prod_id):
    results = db.query('SELECT * FROM product WHERE product.id = $1', prod_id).dictresult()
    return jsonify(results)


@app.route('/api/user/signup', methods=['POST'])
def signup():
    data = request.get_json()
    password = data['password'] # the entered password
    salt = bcrypt.gensalt() # generate a salt
    # now generate the encrypted password
    encrypted_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return jsonify(db.insert('customer', {
        'username': data['username'],
        'email': data['email'],
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'password': encrypted_password
    }))


@app.route('/api/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password'] # the entered password
    customer = db.query('SELECT * FROM customer WHERE customer.username = $1', username).namedresult()[0]
    encrypted_password = customer.password
    customer_id = customer.id
    # the following line will take the original salt that was used
    # in the generation of the encrypted password, which is stored as
    # part of the encrypted_password, and hash it with the entered password
    # (compare lines 25 and 43)
    rehash = bcrypt.hashpw(password.encode('utf-8'), encrypted_password)
    if rehash == encrypted_password:
        token = uuid.uuid4()
        db.insert('auth_token', {
            'token': token,
            'customer_id': customer_id
        })
        user_data = db.query('''
        SELECT customer.username AS "user", auth_token.token as "token"
            FROM customer, auth_token
            WHERE customer.username = $1 AND auth_token.customer_id = $2''', (username, customer_id)).dictresult()
        return jsonify(user_data)
    else:
        return "Incorrect password", 401


@app.route('/api/shopping_cart', methods=['POST'])
def add_product_to_cart():
    data = request.get_json()
    sent_token = data.get('token')
    product_id = data.get('product_id')
    # CURRENT PROBLEM: if customer turns out to be undefined (tokens don't match), the request throws a 500 error. alternatives?
    customer = db.query('SELECT * FROM auth_token WHERE token = $1', sent_token).namedresult()[0]
    customer_id = customer.customer_id
    customer_token = customer.token
    if customer_token:
        db.insert('product_in_shopping_cart', {
            'product_id' : product_id,
            'customer_id' : customer_id
        })
        return jsonify(customer)
    else:
        return "Forbidden", 403


@app.route('/api/shopping_cart')
def view_cart():
    sent_token = request.args.get('token')
    customer_token = db.query('SELECT * FROM auth_token WHERE token = $1', sent_token).namedresult()[0].token
    # same problem from above
    if sent_token == customer_token:
        results = db.query('''
        SELECT product.name
            FROM product_in_shopping_cart
            INNER JOIN product ON product.id = product_id
            INNER JOIN auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
            WHERE auth_token.token = $1''', sent_token).namedresult()
        return jsonify(results)
    else:
        return "Forbidden", 403

@app.route('/api/shopping_cart/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    sent_token = data.get('token')
    customer = db.query('SELECT * FROM auth_token WHERE token = $1', sent_token).namedresult()[0]
    customer_token = customer.token
    # same problem from above
    if sent_token == customer_token:
        customer_id = customer.customer_id
        total_price = db.query("""
        SELECT sum(price)
            FROM product_in_shopping_cart
            INNER JOIN product ON product.id = product_id
            INNER JOIN auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
            WHERE auth_token.token = '48cc7c65-e169-41fa-bada-885cb8c7cab3'""").namedresult()[0].sum
        return jsonify(db.insert('purchase', {
            'customer_id': customer_id,
            'total_price': total_price
        }))
    else:
        return "Forbidden", 403


if __name__ == '__main__':
    app.run(debug=True)
