import sqlite3
import os
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Determine the absolute path for the SQLite database
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "compliments.db")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to our SQLite database and enable dictionary-like row access
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        # Create the compliments table if it doesn't exist yet
        db.execute("""
            CREATE TABLE IF NOT EXISTS compliments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                compliment TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        """)
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database during app startup
init_db()

@app.route('/')
def index():
    return "Compliment API is Live! Spread kindness responsibly."

# GET endpoint to retrieve the most recent compliment
@app.route('/compliment', methods=['GET'])
def get_last_compliment():
    try:
        db = get_db()
        cursor = db.execute("SELECT name, compliment, timestamp FROM compliments ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return jsonify({
                "name": row["name"],
                "compliment": row["compliment"]
            }), 200
        else:
            return jsonify({
                "name": "",
                "compliment": "No compliments yet! Be the first to share some kindness."
            }), 200
    except Exception as e:
        app.logger.error(f"Error getting compliment: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# POST endpoint to add a new compliment
@app.route('/compliment', methods=['POST'])
def add_compliment():
    try:
        data = request.get_json()
        name = data.get("name")
        compliment = data.get("compliment")
        if not name or not compliment:
            return jsonify({"error": "Name and compliment are required."}), 400

        timestamp = datetime.utcnow().isoformat()
        db = get_db()
        db.execute(
            "INSERT INTO compliments (name, compliment, timestamp) VALUES (?, ?, ?)",
            (name, compliment, timestamp)
        )
        db.commit()
        return jsonify({"message": "Compliment added! Spread the love!"}), 201
    except Exception as e:
        app.logger.error(f"Error adding compliment: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    # For production, run this through a WSGI server (e.g., Gunicorn)
    # For local testing, enable debug mode.
    app.run(host="0.0.0.0", debug=False)
