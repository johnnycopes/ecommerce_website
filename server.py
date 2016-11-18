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
    results = db.query('SELECT * FROM customer WHERE customer.username = $1', username).namedresult()[0]
    encrypted_password = results.password
    customer_id = results.id
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
        user_data = db.query('SELECT customer.username as "user", auth_token.token as "token" FROM customer, auth_token WHERE customer.username = $1 AND auth_token.customer_id = $2', (username, customer_id)).dictresult()
        return jsonify(user_data)
    else:
        return "Incorrect password", 401
    return rehash

if __name__ == '__main__':
    app.run(debug=True)
