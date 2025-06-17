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

# --- Route: Get phrases by level ---
@app.route('/phrases/level/<level>', methods=['GET'])
def get_phrases_by_level(level):
    slow_down_if_suspicious()
    print("lo kig ki")
    offset = int(request.args.get('offset', 0))  # default 0
    limit = int(request.args.get('limit', 200))  # default 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phrase FROM phraseTable WHERE level = %s LIMIT %s OFFSET %s",
        (level, limit, offset)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    phrases = [row[0] for row in rows]
    return jsonify(phrases)


# --- Route: Search phrases by level ---
@app.route('/phrases/level_search/<searchByLevel>', methods=['GET'])
def search_phrases_by_level(searchByLevel):
    slow_down_if_suspicious()
    query = request.args.get('query', '').strip()
    if len(query) < 5:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phrase FROM phraseTable WHERE level = %s AND phrase ILIKE %s",
        (searchByLevel, f"%{query}%")
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    phrases = [row[0] for row in rows]
    return jsonify(phrases)

# --- Route: Add phrases---
@app.route('/3456k34/phrases/add', methods=['POST'])
def add_phrase():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(SN) FROM phraseTable")
    max_sn = cursor.fetchone()[0]
    next_sn = (max_sn or 0) + 1

    data = request.form
    phrase = data.get('phrase', '').strip()
    english_meaning = data.get('english_meaning', '').strip()
    hindi_meaning = data.get('hindi_meaning', '').strip()
    example = data.get('example', '').strip()
    level = data.get('level', '').strip()

#    if not all([phrase, english_meaning, hindi_meaning, example]):
 #       return make_response(jsonify({'status': 'error', 'message': 'All fields are required.'}), 400)



    # Check if the phrase already exists
    cursor.execute("SELECT 1 FROM phraseTable WHERE phrase = %s", (phrase,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return make_response(jsonify({'status': 'exists', 'message': 'Phrase already exists in the database.'}), 200)

    # Insert the phrase
    cursor.execute(
        "INSERT INTO phraseTable (SN, phrase, english_meaning, hindi_meaning, example, level) VALUES (%s, %s, %s, %s, %s, %s)",
        (next_sn, phrase, english_meaning, hindi_meaning, example, level)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Phrase added successfully.'})


# --- Route: Get Credentials ---
@app.route('/phrases/creds', methods=['GET'])
def get_credentials():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cred_name, cred_val FROM credentials")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        fetched_credentials = {row[0]: row[1] for row in rows}

        # Fill in any missing values with defaults
       # final_credentials = DEFAULT_CREDENTIALS.copy()
        #final_credentials.update(fetched_credentials)

        return jsonify(fetched_credentials)

    except Exception as e:
        print(f"[ERROR] Fetching credentials failed: {e}")
#        return jsonify(DEFAULT_CREDENTIALS)

if __name__ == '__main__':
    app.run(debug=True)
