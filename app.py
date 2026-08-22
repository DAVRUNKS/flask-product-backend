from flask import Flask, jsonify, request
import sqlite3
import hashlib

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/init", methods=["GET"])
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    return jsonify({"message": "Database init complete"})


@app.route("/")
def home():
    return jsonify({"message": "Hello from our first server"})


@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()

    rows = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json()

    name = data.get("name")
    price = data.get("price")

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, price) VALUES (?, ?)",
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
        "message": "product added",
        "product": new_product
    }), 201
    
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = get_db_connection()

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "User registered successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}),409
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username,hashed_password)).fetchone()
    conn.close()
    
    if user:
        return jsonify({"message": f"Welcome {username}!"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    

if __name__ == "__main__":
    app.run(debug=True)
    