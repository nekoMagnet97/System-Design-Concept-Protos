"""
Demonstration of an API server that is explicitly aware of a sharded database topology.
This script shows how the server determines the appropriate database shard for a given user_id 
and routes requests to the correct backend database accordingly.

Sample curl usage:

curl -X POST http://localhost:9000/heartbeats \
  -H "Content-Type: application/json" \
  -d '{"user_id":20}'

curl http://localhost:9000/heartbeats/status/1234
"""

import atexit
import time
import mysql.connector
from flask import Flask, jsonify, request

app = Flask(__name__)
DBs = []

def init_db():
    global DBs
    db1 = mysql.connector.connect(
        host="localhost",
        port=8080,
        user="root",
        password="",
        database="test_db"
    )
    db2 = mysql.connector.connect(
        host="localhost",
        port=8080,
        user="root",
        password="",
        database="test_db"
    )
    DBs = [db1, db2]


def getShardIndex(userId):
    index = int(userId) % len(DBs)
    print(f"Using DB {index}")
    return index


def close_dbs():
    for db in DBs:
        try:
            db.close()
        except mysql.connector.Error:
            pass


atexit.register(close_dbs)


@app.route('/heartbeats', methods=['POST'])
def create_heartbeat():
    data = request.get_json(silent=True) or {}
    userID = data.get('user_id')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    if userID is None:
        return jsonify({'error': 'user_id is required'}), 400

    db = DBs[getShardIndex(userID)]
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "REPLACE INTO heartbeats (userID, last_hb) VALUES (%s, %s);",
                (userID, timestamp),
            )
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        return jsonify({'error': 'failed to save heartbeat', 'detail': str(e)}), 500

    return jsonify({'message': 'ok'})


@app.route('/heartbeats/status/<int:user_id>', methods=['GET'])
def get_heartbeat_status(user_id):
    db = DBs[getShardIndex(user_id)]
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT last_hb FROM heartbeats WHERE userID = %s;",
                (user_id,),
            )
            result = cursor.fetchone()
    except mysql.connector.Error as e:
        return jsonify({'error': 'failed to read heartbeat', 'detail': str(e)}), 500

    if result is None:
        return jsonify({'is_online': False})
    
    return jsonify({
        'response': result, 
        'is_online': result[0].timestamp() > (time.time() - 300)
        })
    # return jsonify({'response': result})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=9000)
