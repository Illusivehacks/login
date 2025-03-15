from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import bcrypt
from datetime import datetime

app = Flask(__name__)

# Database setup
def create_connection():
    conn = sqlite3.connect("food_ordering.db")
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        age INTEGER,
        gender TEXT,
        security_question TEXT NOT NULL,
        security_answer TEXT NOT NULL,
        password_hash TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MenuItem (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        image_path TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OrderTable (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customer (customer_id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OrderItem (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES OrderTable (order_id),
        FOREIGN KEY (item_id) REFERENCES MenuItem (item_id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES OrderTable (order_id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ActivityLog (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

# Sample data
def populate_sample_data():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO Customer (username, email, age, gender, security_question, security_answer, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   ("joy", "joy@example.com", 25, "female", "What is your pet’s name?", bcrypt.hashpw(b"Fluffy", bcrypt.gensalt()).decode('utf-8'), bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode('utf-8')))
    cursor.execute("INSERT OR IGNORE INTO MenuItem (name, price, description, image_path) VALUES (?, ?, ?, ?)",
                   ("Pizza", 10.99, "Delicious cheese pizza", "pizza.jpg"))
    cursor.execute("INSERT OR IGNORE INTO MenuItem (name, price, description, image_path) VALUES (?, ?, ?, ?)",
                   ("Burger", 8.99, "Juicy beef burger", "burger.jpg"))
    conn.commit()
    conn.close()

# Log activity
def log_activity(activity):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ActivityLog (activity, timestamp) VALUES (?, ?)",
                   (activity, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Initialize database and populate sample data
create_tables()
populate_sample_data()

# Routes
@app.route('/')
def home():
    return render_template('authentication.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    role = data['role']

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Customer WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[7].encode('utf-8')):  # Check password hash
        log_activity(f"User {user[1]} logged in")
        return jsonify({'success': True, 'role': user[6]})  # Assuming role is stored in the 7th column
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    email = data['email']
    age = data['age']
    gender = data['gender']
    security_question = data['security_question']
    security_answer = data['security_answer']
    password = data['password']

    # Hash password and security answer
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    security_answer_hash = bcrypt.hashpw(security_answer.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO Customer (username, email, age, gender, security_question, security_answer, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (username, email, age, gender, security_question, security_answer_hash, password_hash))
        conn.commit()
        log_activity(f"New user registered: {username}")
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username or email already exists'})
    finally:
        conn.close()

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/menu')
def menu():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM MenuItem')
    menu_items = cursor.fetchall()
    conn.close()
    return jsonify(menu_items)

if __name__ == '__main__':
    app.run(debug=True)