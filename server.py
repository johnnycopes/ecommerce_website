from flask import Flask, jsonify, request, redirect
import pg
import os

db = pg.DB(dbname='ecommerce_db')
app = Flask('ecommerceApp')

@app.route('/api/products')
def products():
    results = db.query('SELECT * from product').dictresult()
    return jsonify(results)

@app.route('/api/products/<prod_id>')
def products_prod_id(prod_id):
    results = db.query('SELECT * from product where product.id = $1', prod_id).dictresult()
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
