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
    print data
    sent_token = data.get('token')
    print sent_token
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


@app.route('/api/shopping_cart', methods=["GET"])
def view_cart():
    get_token = request.args.get('token')
    customer_id = db.query('''
    SELECT
        customer.id
    FROM
        customer, auth_token
    WHERE
        customer.id = auth_token.customer_id AND
        now() < token_expires AND
        auth_token.token = $1
    ''', get_token).namedresult()
    if customer_id == []:
        return 'Forbidden', 403
    else:
        product_query = db.query('''
        SELECT
            product.name, product.image_path, product.price, product.id AS "product_id"
        FROM
            product, product_in_shopping_cart, customer
        WHERE
            product.id = product_in_shopping_cart.product_id AND product_in_shopping_cart.customer_id = customer.id AND
            customer.id = $1;
        ''', customer_id[0].id).dictresult()
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
                auth_token.token = $1""", get_token).namedresult()[0].sum
        return jsonify({
            'product_query': product_query,
            'total_price': total_price
        })


@app.route('/api/shopping_cart/checkout', methods=["POST"])
def checkout():
    post_token = request.get_json().get('token')
    print 'this is the post_token', post_token
    formData = request.get_json()
    print 'this is formData', formData
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
        return jsonify(purchase)


if __name__ == '__main__':
    app.run(debug=True)
