from flask import Flask, jsonify, request, redirect
import bcrypt, uuid, pg, os


db = pg.DB(dbname='ecommerce_db')
app = Flask('ecommerce', static_url_path="")


@app.route('/')
def home():
    return app.send_static_file('index.html')


@app.route('/api/products')
def products():
    product_list = db.query('SELECT * FROM product').dictresult()
    return jsonify(product_list)


@app.route('/api/product/<prod_id>')
def products_details(prod_id):
    product_details = db.query('SELECT * FROM product WHERE product.id = $1', prod_id).dictresult()[0]
    return jsonify(product_details)


@app.route('/api/user/signup', methods=['POST'])
def signup():
    data = request.get_json()
    password = data['password'] # the entered password
    salt = bcrypt.gensalt() # generate a salt
    # generate the encrypted password
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
        token = uuid.uuid4()
        user = db.query('SELECT id, first_name FROM customer WHERE username = $1', username).namedresult()[0]
        db.insert (
            "auth_token",
            token = token,
            customer_id = user.id
        )
        login_data = {
            'token': token,
            'customer_id': user.id,
            'username' : user.first_name
        }
        return jsonify(login_data)
    else:
        return "Incorrect password", 401


@app.route('/api/shopping_cart', methods=['POST'])
def add_product_to_cart():
    data = request.get_json()
    sent_token = data.get('token')
    product_id = data.get('product_id')
    customer = db.query('SELECT * FROM auth_token WHERE token = $1 AND now() < token_expires', sent_token).namedresult()
    if customer == []:
        return "Forbidden", 403
    else:
        customer_id = customer[0].customer_id
        customer_token = customer[0].token
        db.insert('product_in_shopping_cart', {
            'product_id' : product_id,
            'customer_id' : customer_id
        })
        return jsonify(customer)


@app.route('/api/shopping_cart')
def view_cart():
    sent_token = request.args.get('token')
    customer = db.query('SELECT * FROM auth_token WHERE token = $1 AND now() < token_expires', sent_token).namedresult()
    if customer == []:
        return "Forbidden", 403
    else:
        results = db.query('''
        SELECT product.name
            FROM product_in_shopping_cart
            INNER JOIN product ON product.id = product_id
            INNER JOIN auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
            WHERE auth_token.token = $1''', sent_token).namedresult()
        return jsonify(results)


@app.route('/api/shopping_cart/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    sent_token = data.get('token')
    customer = db.query('SELECT * FROM auth_token WHERE token = $1 AND now() < token_expires', sent_token).namedresult()
    if customer == []:
        return "Forbidden", 403
    else:
        customer_id = customer[0].customer_id
        customer_token = customer[0].token
        total_price = db.query("""
        SELECT sum(price)
            FROM product_in_shopping_cart
            INNER JOIN product ON product.id = product_id
            INNER JOIN auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
            WHERE auth_token.token = $1""", customer_token).namedresult()[0].sum
        purchased_items = db.query("""
        SELECT price, product.name, product.id
            FROM product_in_shopping_cart
            INNER JOIN product ON product.id = product_id
            INNER JOIN auth_token ON auth_token.customer_id = product_in_shopping_cart.customer_id
            WHERE auth_token.token = $1""", customer_token).dictresult()
        purchase = db.insert('purchase', {
            'customer_id': customer_id,
            'total_price': total_price
        })
        for item in purchased_items:
            db.insert('product_in_purchase', {
                'product_id': item['id'],
                'purchase_id': purchase['id']
            })
        db.query('DELETE FROM product_in_shopping_cart WHERE customer_id = $1', customer_id)
        return jsonify(purchase)


if __name__ == '__main__':
    app.run(debug=True)
