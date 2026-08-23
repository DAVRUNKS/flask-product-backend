from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Allow requests from your frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://127.0.0.1:5500",
            "http://localhost:5500"
        ]
    }
})
# =========================
# DATABASE
# =========================

DATABASE = "products.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# TOKEN AUTHENTICATION
# =========================

API_TOKEN = os.getenv("API_TOKEN")


def require_token(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({
                "error": "Authorization token required"
            }), 401

        if token != f"Bearer {API_TOKEN}":
            return jsonify({
                "error": "Invalid token"
            }), 403

        return f(*args, **kwargs)

    return decorated_function


# =========================
# HOME
# =========================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Flask Product API is running"
    })


# =========================
# GET PRODUCTS
# =========================

@app.route("/products", methods=["GET"])
def get_products():

    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(product)
        for product in products
    ])


# =========================
# ADD PRODUCT
# =========================

@app.route("/products", methods=["POST"])
def add_product():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data required"
        }), 400

    name = data.get("name")
    price = data.get("price")

    if not name or price is None:
        return jsonify({
            "error": "Name and price are required"
        }), 400

    try:
        price = float(price)
    except ValueError:
        return jsonify({
            "error": "Price must be a number"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO products (name, price)
        VALUES (?, ?)
        """,
        (name, price)
    )

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "Product added successfully",
        "id": new_id,
        "name": name,
        "price": price
    }), 201


# =========================
# REGISTER USER
# =========================

@app.route("/register", methods=["POST"])
def register_user():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    # Hash password
    hashed_password = hashlib.sha256(
        password.encode()
    ).hexdigest()

    conn = get_db_connection()

    try:

        conn.execute(
            """
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """,
            (username, hashed_password)
        )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "error": "Username already exists"
        }), 409

    conn.close()

    return jsonify({
        "message": "User registered successfully"
    }), 201


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )