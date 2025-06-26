# app.py
from flask import Flask, request, jsonify
from flask import make_response
import psycopg2
import os
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import logging
import json  # ✅ ADD THIS LINE
import traceback
import binascii

AES_KEY = binascii.unhexlify(os.environ.get('AES_KEY'))  # 32 bytes
AES_IV = binascii.unhexlify(os.environ.get('AES_IV'))    # 16 bytes
app = Flask(__name__)

def encrypt_data_aes(raw_data: str) -> str:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    encrypted = cipher.encrypt(pad(raw_data.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode()

# Database connection using environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', 5432)
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

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



#Get all the data att once encrypted
@app.route('/phrases/all/encrypted', methods=['GET'])
def get_all_phrases_encrypted():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT phrase, english_meaning, hindi_meaning, example, level FROM phraseTable")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [
            {
                'phrase': row[0],
                'english_meaning': row[1],
                'hindi_meaning': row[2],
                'example': row[3],
                'level': row[4]
            }
            for row in rows
        ]

        json_data = json.dumps(data)
        # print("[SERVER] JSON before encryption:", json_data)
        print("Ek request shi se dedi...")
        

        encrypted = encrypt_data_aes(json_data)
        print("[SERVER] Encrypted base64:", encrypted[:100], "...")

        return jsonify({'data': encrypted})

    except Exception as e:
        print("[SERVER] ERROR in encryption route:", str(e))
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


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

        # Prevent caching
        response = make_response(jsonify(fetched_credentials))
        response.headers['Cache-Control'] = 'no-store'
        return response

    except Exception as e:
        print(f"[ERROR] Fetching credentials failed: {e}")
        return jsonify({})  # Return something even on failure

if __name__ == '__main__':
    app.run(debug=True)
