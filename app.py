# app.py
from flask import Flask, request, jsonify
import psycopg2
import os
import time

app = Flask(__name__)

# Database connection using environment variables
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'phrases'
DB_USER = 'postgres'
DB_PASSWORD = '1928'
#DB_HOST = os.environ.get('DB_HOST')
#DB_PORT = os.environ.get('DB_PORT', 5432)
#DB_NAME = os.environ.get('DB_NAME')
#DB_USER = os.environ.get('DB_USER')
#DB_PASSWORD = os.environ.get('DB_PASSWORD')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# --- Helper function to slow down suspicious requests ---
def slow_down_if_suspicious():
    user_agent = request.headers.get('User-Agent', '')
    if "python" in user_agent.lower() or "postman" in user_agent.lower():
        # Suspect it might be a bot/script -> slow down
        time.sleep(3)

# --- Route: Get phrases by level ---
@app.route('/phrases/level/<level>', methods=['GET'])
def get_phrases_by_level(level):
    slow_down_if_suspicious()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phrase FROM phraseTable WHERE level = %s", (level,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    phrases = [row[0] for row in rows]
    return jsonify(phrases)

# --- Route: Search phrases ---
@app.route('/phrases/search', methods=['GET'])
def search_phrases():
    slow_down_if_suspicious()
    query = request.args.get('query', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phrase FROM phraseTable WHERE phrase ILIKE %s", ('%' + query + '%',))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    phrases = [row[0] for row in rows]
    return jsonify(phrases)

# --- Route: Get full phrase details ---
@app.route('/phrases/details', methods=['GET'])
def get_phrase_details():
    slow_down_if_suspicious()
    phrase = request.args.get('phrase', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT phrase, english_meaning, hindi_meaning, example
        FROM phraseTable
        WHERE phrase = %s
    """, (phrase,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        phrase_detail = {
            'phrase': row[0],
            'english_meaning': row[1],
            'hindi_meaning': row[2],
            'example': row[3]
        }
        return jsonify(phrase_detail)
    else:
        return jsonify({'error': 'Phrase not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
