from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging
import csv
import io

load_dotenv()  # .env 파일에서 환경 변수 로드

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB 연결 설정
mongo_client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
db = mongo_client.baby_growth
users_collection = db.users
records_collection = db.records

# 로깅 설정
logging.basicConfig(level=logging.INFO)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    print(f'Attempting to log in with username: {username} and password: {password}')

    # 예시: admin 계정만 허용
    if username == 'admin' and password == 'admin':
        return jsonify({'username': username})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/records', methods=['GET'])
def get_records():
    records = list(records_collection.find())
    for record in records:
        record['_id'] = str(record['_id'])
    return jsonify(records)

@app.route('/api/records', methods=['POST'])
def add_record():
    data = request.json
    record_id = records_collection.insert_one(data).inserted_id
    return jsonify(str(record_id)), 201

@app.route('/api/records/<record_id>', methods=['PUT'])
def update_record(record_id):
    data = request.json
    records_collection.update_one({'_id': ObjectId(record_id)}, {'$set': data})
    return jsonify({'msg': 'Record updated'})

@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    try:
        record_id_obj = ObjectId(record_id)
    except errors.InvalidId:
        return jsonify({'error': 'Invalid record ID'}), 400

    result = records_collection.delete_one({'_id': record_id_obj})
    if result.deleted_count == 0:
        return jsonify({'error': 'Record not found'}), 404

    return jsonify({'msg': 'Record deleted'})

# 관리자용 엔드포인트
@app.route('/api/admin/records', methods=['GET'])
def admin_get_records():
    records = list(records_collection.find())
    for record in records:
        record['_id'] = str(record['_id'])
    return jsonify(records)

@app.route('/api/admin/records', methods=['DELETE'])
def admin_clear_records():
    records_collection.delete_many({})
    return jsonify({'msg': 'All records deleted'})

@app.route('/api/admin/records/upload', methods=['POST'])
def admin_upload_records():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    header = next(csv_input)

    for row in csv_input:
        record = {header[i]: row[i] for i in range(len(header))}
        records_collection.insert_one(record)
    
    return jsonify({'msg': 'Records uploaded successfully'})

@app.route('/api/admin/records/download', methods=['GET'])
def admin_download_records():
    records = list(records_collection.find())
    for record in records:
        record['_id'] = str(record['_id'])

    si = io.StringIO()
    cw = csv.writer(si)
    if records:
        cw.writerow(records[0].keys())
        for record in records:
            cw.writerow(record.values())

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=records.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

