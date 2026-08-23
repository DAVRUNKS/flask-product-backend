from flask import Flask, jsonify, request
import sqlite3
import os
import secrets
from functools import wraps
from dotenv import load_dotenv
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

API_TOKEN = os.getenv("API_TOKEN")

# -----------------------------
# Database
# -----------------------------

def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# API Token Authentication
# -----------------------------

def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        authorization = request.headers.get("Authorization")

        if not authorization:
            return jsonify({
                "error": "Authorization header missing"
            }), 401

        if not authorization.startswith("Bearer "):
            return jsonify({
                "error": "Invalid authorization format"
            }), 401

        token = authorization.split(" ", 1)[1]

        if not API_TOKEN:
            return jsonify({
                "error": "API token is not configured"
            }), 500

        if not secrets.compare_digest(token, API_TOKEN):
            return jsonify({
                "error": "Unauthorized"
            }), 401

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------
# Initialize Database
# -----------------------------

@app.route("/init", methods=["GET"])
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

    return jsonify({
        "message": "Database init complete"
    })


# -----------------------------
# Home
# -----------------------------

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Hello from our first server"
    })


# -----------------------------
# Get Products
# -----------------------------

@app.route("/products", methods=["GET"])
@require_token
def get_products():

    conn = get_db_connection()

    rows = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    products = [dict(row) for row in rows]

    return jsonify(products)


# -----------------------------
# Add Product
# -----------------------------

@app.route("/products", methods=["POST"])
@require_token
def add_product():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    price = data.get("price")

    if not name or price is None:
        return jsonify({
            "error": "Name and price are required"
        }), 400

    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Price must be a number"
        }), 400

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, price)
        VALUES (?, ?)
        """,
        (name, price)
    )

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    new_product = {
        "id": new_id,
        "name": name,
        "price": price
    }

    return jsonify({
        "message": "Product added",
        "product": new_product
    }), 201


# -----------------------------
# Register
# -----------------------------

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Missing username or password"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    hashed_password = generate_password_hash(password)

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


# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Missing username or password"
        }), 400

    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    conn.close()

    if not user:
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    if not check_password_hash(user["password"], password):
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    return jsonify({
        "message": f"Welcome {username}!"
    })


# -----------------------------
# Run Server
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)